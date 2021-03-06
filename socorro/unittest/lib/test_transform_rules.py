# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_
from mock import Mock

from configman.dotdict import DotDict
from configman import Namespace

from socorro.lib import transform_rules
from socorro.unittest.testbase import TestCase


def assert_expected(actual, expected):
    assert actual == expected, "expected:\n%s\nbut got:\n%s" % (str(expected),
                                                                str(actual))

def assert_expected_same(actual, expected):
    assert actual == expected, "expected:\n%s\nbut got:\n%s" % (expected,
                                                                actual)

def foo(s, d):
    pass

def bar(s, d):
    pass


#==============================================================================
class TestRuleTestLaughable(transform_rules.Rule):
    required_config = Namespace()
    required_config.add_option('laughable', default='fred')

    def _predicate(self, *args, **kwargs):
        return self.config.laughable != 'fred'


#==============================================================================
class TestRuleTestDangerous(transform_rules.Rule):
    required_config = Namespace()
    required_config.add_option('dangerous', default='sally')

    def _action(self, *args, **kwargs):
        return self.config.dangerous != 'sally'


#==============================================================================
class TestTransformRules(TestCase):

    def test_kw_str_parse(self):
        a = 'a=1, b=2'
        actual = transform_rules.kw_str_parse(a)
        expected = {'a':1, 'b':2}
        assert_expected(expected, actual)

        a = 'a="fred", b=3.1415'
        actual = transform_rules.kw_str_parse(a)
        expected = {'a':'fred', 'b':3.1415}
        assert_expected(expected, actual)

    def test_TransfromRule_init(self):
        r = transform_rules.TransformRule(True, (), {}, True, (), {})
        assert_expected(r.predicate, True)
        assert_expected(r.predicate_args, ())
        assert_expected(r.predicate_kwargs, {})
        assert_expected(r.action, True)
        assert_expected(r.action_args, ())
        assert_expected(r.action_kwargs, {})

        r = transform_rules.TransformRule(True, '', '', True, '', '')
        assert_expected(r.predicate, True)
        assert_expected(r.predicate_args, ())
        assert_expected(r.predicate_kwargs, {})
        assert_expected(r.action, True)
        assert_expected(r.action_args, ())
        assert_expected(r.action_kwargs, {})

        r = transform_rules.TransformRule(foo, '', '', bar, '', '')
        assert_expected(r.predicate, foo)
        assert_expected(r.predicate_args, ())
        assert_expected(r.predicate_kwargs, {})
        assert_expected(r.action, bar)
        assert_expected(r.action_args, ())
        assert_expected(r.action_kwargs, {})

        r = transform_rules.TransformRule('socorro.unittest.lib.test_transform_rules.foo', '', '',
                        'socorro.unittest.lib.test_transform_rules.bar', '', '')
        repr_pred = repr(r.predicate)
        assert 'foo' in repr_pred, 'expected "foo" in %s' % repr_pred
        assert_expected(r.predicate_args, ())
        assert_expected(r.predicate_kwargs, {})
        repr_act = repr(r.action)
        assert 'bar' in repr_act, 'expected "bar" in %s' % repr_act
        assert_expected(r.action_args, ())
        assert_expected(r.action_kwargs, {})

        r = transform_rules.TransformRule('socorro.unittest.lib.test_transform_rules.foo',
                                          (1,),
                                          {'a':13},
                                          'socorro.unittest.lib.test_transform_rules.bar',
                                          '',
                                          '')
        repr_pred = repr(r.predicate)
        assert 'foo' in repr_pred, 'expected "foo" in %s' % repr_pred
        assert_expected(r.predicate_args, (1,))
        assert_expected(r.predicate_kwargs, {'a':13})
        repr_act = repr(r.action)
        assert 'bar' in repr_act, 'expected "bar" in %s' % repr_act
        assert_expected(r.action_args, ())
        assert_expected(r.action_kwargs, {})

        r = transform_rules.TransformRule('socorro.unittest.lib.test_transform_rules.foo',
                                          '1, 2',
                                          'a=13',
                                          'socorro.unittest.lib.test_transform_rules.bar',
                                          '',
                                          '')
        repr_pred = repr(r.predicate)
        assert 'foo' in repr_pred, 'expected "foo" in %s' % repr_pred
        assert_expected(r.predicate_args, (1,2))
        assert_expected(r.predicate_kwargs, {'a':13})
        repr_act = repr(r.action)
        assert 'bar' in repr_act, 'expected "bar" in %s' % repr_act
        assert_expected(r.action_args, ())
        assert_expected(r.action_kwargs, {})

    def test_TransformRule_with_class(self):
        """test to make sure that classes can be used as predicates and
        actions"""
        class MyRule(object):
            def __init__(self, config=None):
                self.predicate_called = False
                self.action_called = False
            def predicate(self):
                self.predicate_called = True
                return True
            def action(self):
                self.action_called = True
                return True
        r = transform_rules.TransformRule(
            MyRule, (), {},
            MyRule, (), {}
        )
        eq_(r.predicate, r._predicate_implementation.predicate)
        eq_(r.action, r._action_implementation.action)
        eq_(r._action_implementation, r._predicate_implementation)
        r.act()
        ok_(r._predicate_implementation.predicate_called)
        ok_(r._action_implementation.action_called)

    def test_TransformRule_with_class_function_mix(self):
        """test to make sure that classes can be mixed with functions as
        predicates and actions"""
        class MyRule(object):
            def __init__(self, config=None):
                self.predicate_called = False
                self.action_called = False
            def predicate(self):
                self.predicate_called = True
                return True
            def action(self):
                self.action_called = True
                return True

        def my_predicate():
            return True

        r = transform_rules.TransformRule(
            my_predicate, (), {},
            MyRule, (), {}
        )
        eq_(r.predicate, my_predicate)
        eq_(r.action, r._action_implementation.action)
        self.assertNotEqual(r._action_implementation, r._predicate_implementation)
        r.act()
        # make sure that the class predicate function was not called
        ok_(not r._action_implementation.predicate_called)
        ok_(r._action_implementation.action_called)


    def test_TransfromRule_function_or_constant(self):
        r = transform_rules.TransformRule.function_invocation_proxy(True,
                                                                    (),
                                                                    {})
        assert_expected(r, True)
        r = transform_rules.TransformRule.function_invocation_proxy(False,
                                                                    (),
                                                                    {})
        assert_expected(r, False)

        r = transform_rules.TransformRule.function_invocation_proxy(True,
                                                                    (1, 2, 3),
                                                                    {})
        assert_expected(r, True)
        r = transform_rules.TransformRule.function_invocation_proxy(False,
                                                                    (),
                                                                    {'a':13})
        assert_expected(r, False)

        r = transform_rules.TransformRule.function_invocation_proxy('True',
                                                                    (1, 2, 3),
                                                                    {})
        assert_expected(r, True)
        r = transform_rules.TransformRule.function_invocation_proxy(None,
                                                                    (),
                                                                    {'a':13})
        assert_expected(r, False)

        def fn1(*args, **kwargs):
            return (args, kwargs)

        r = transform_rules.TransformRule.function_invocation_proxy(fn1,
                                                                    (1, 2, 3),
                                                                    {})
        assert_expected(r, ((1, 2, 3), {}))
        r = transform_rules.TransformRule.function_invocation_proxy(fn1,
                                                                    (1, 2, 3),
                                                                    {'a':13})
        assert_expected(r, ((1, 2, 3), {'a':13}))


    def test_TransfromRule_act(self):
        rule = transform_rules.TransformRule(True, (), {}, True, (), {})
        r = rule.act()
        assert_expected(r, (True, True))

        rule = transform_rules.TransformRule(True, (), {}, False, (), {})
        r = rule.act()
        assert_expected(r, (True, False))

        def pred1(s, d, fred):
            return bool(fred)
        s = {'dwight': 96}
        d = {}

        rule = transform_rules.TransformRule(pred1, (True), {}, False, (), {})
        r = rule.act(s, d)
        assert_expected(r, (True, False))

        rule = transform_rules.TransformRule(pred1, (), {'fred':True},
                                             False, (), {})
        r = rule.act(s, d)
        assert_expected(r, (True, False))

        rule = transform_rules.TransformRule(pred1, (), {'fred':False},
                                             False, (), {})
        r = rule.act(s, d)
        assert_expected(r, (False, None))

        def copy1(s, d, s_key, d_key):
            d[d_key] = s[s_key]
            return True

        rule = transform_rules.TransformRule(pred1, (), {'fred':True},
                                             copy1, (),
                                               's_key="dwight", d_key="wilma"')
        r = rule.act(s, d)
        assert_expected(r, (True, True))
        assert_expected(s['dwight'], 96)
        assert_expected(d['wilma'], 96)


    def test_TransformRuleSystem_init(self):
        rules = transform_rules.TransformRuleSystem()
        assert_expected(rules.rules, [])

    def test_TransformRuleSystem_load_rules(self):
        rules = transform_rules.TransformRuleSystem()
        some_rules = [(True, '', '', True, '', ''),
                      (False, '', '', False, '', '')]
        rules.load_rules(some_rules)
        expected = [transform_rules.TransformRule(*(True, (), {},
                                                    True, (), {})),
                    transform_rules.TransformRule(*(False, (), {},
                                                    False, (), {}))]
        assert_expected_same(rules.rules, expected)

    def test_TransformRuleSystem_append_rules(self):
        rules = transform_rules.TransformRuleSystem()
        some_rules = [(True, '', '', True, '', ''),
                      (False, '', '', False, '', '')]
        rules.append_rules(some_rules)
        expected = [transform_rules.TransformRule(*(True, (), {},
                                                    True, (), {})),
                    transform_rules.TransformRule(*(False, (), {},
                                                    False, (), {}))]
        assert_expected_same(rules.rules, expected)

    def test_TransformRuleSystem_apply_all_rules(self):

        quit_check_mock = Mock()

        def assign_1(s, d):
            d['one'] = 1
            return True

        def increment_1(s, d):
            try:
                d['one'] += 1
                return True
            except KeyError:
                return False

        some_rules = [(True, '', '', increment_1, '', ''),
                      (True, '', '', assign_1, '', ''),
                      (False, '', '', increment_1, '', ''),
                      (True, '', '', increment_1, '', ''),
                     ]
        rules = transform_rules.TransformRuleSystem(quit_check=quit_check_mock)
        rules.load_rules(some_rules)
        s = {}
        d = {}
        rules.apply_all_rules(s, d)
        assert_expected(d, {'one': 2})
        assert_expected(quit_check_mock.call_count, 4)

    def test_TransformRuleSystem_apply_all_until_action_succeeds(self):

        quit_check_mock = Mock()

        def assign_1(s, d):
            d['one'] = 1
            return True

        def increment_1(s, d):
            try:
                d['one'] += 1
                return True
            except KeyError:
                return False

        some_rules = [(True, '', '', increment_1, '', ''),
                      (True, '', '', assign_1, '', ''),
                      (False, '', '', increment_1, '', ''),
                      (True, '', '', increment_1, '', ''),
                     ]
        rules = transform_rules.TransformRuleSystem(quit_check=quit_check_mock)
        rules.load_rules(some_rules)
        s = {}
        d = {}
        rules.apply_until_action_succeeds(s, d)
        assert_expected(d, {'one': 1})
        assert_expected(quit_check_mock.call_count, 2)


    def test_TransformRuleSystem_apply_all_until_action_fails(self):

        quit_check_mock = Mock()

        def assign_1(s, d):
            d['one'] = 1
            return True

        def increment_1(s, d):
            try:
                d['one'] += 1
                return True
            except KeyError:
                return False

        some_rules = [(True, '', '', increment_1, '', ''),
                      (True, '', '', assign_1, '', ''),
                      (False, '', '', increment_1, '', ''),
                      (True, '', '', increment_1, '', ''),
                     ]
        rules = transform_rules.TransformRuleSystem(quit_check=quit_check_mock)
        rules.load_rules(some_rules)
        s = {}
        d = {}
        rules.apply_until_action_fails(s, d)
        assert_expected(d, {})
        assert_expected(quit_check_mock.call_count, 1)


    def test_TransformRuleSystem_apply_all_until_predicate_succeeds(self):

        quit_check_mock = Mock()

        def assign_1(s, d):
            d['one'] = 1
            return True

        def increment_1(s, d):
            try:
                d['one'] += 1
                return True
            except KeyError:
                return False

        some_rules = [(True, '', '', increment_1, '', ''),
                      (True, '', '', assign_1, '', ''),
                      (False, '', '', increment_1, '', ''),
                      (True, '', '', increment_1, '', ''),
                     ]
        rules = transform_rules.TransformRuleSystem(quit_check=quit_check_mock)
        rules.load_rules(some_rules)
        s = {}
        d = {}
        rules.apply_until_predicate_succeeds(s, d)
        assert_expected(d, {})
        assert_expected(quit_check_mock.call_count, 1)

    def test_TransformRuleSystem_apply_all_until_predicate_fails(self):

        quit_check_mock = Mock()

        def assign_1(s, d):
            d['one'] = 1
            return True

        def increment_1(s, d):
            try:
                d['one'] += 1
                return True
            except KeyError:
                return False

        some_rules = [(True, '', '', increment_1, '', ''),
                      (True, '', '', assign_1, '', ''),
                      (False, '', '', increment_1, '', ''),
                      (True, '', '', increment_1, '', ''),
                     ]
        rules = transform_rules.TransformRuleSystem(quit_check=quit_check_mock)
        rules.load_rules(some_rules)
        s = {}
        d = {}
        rules.apply_until_predicate_fails(s, d)
        assert_expected(d, {'one': 1})

        some_rules = [
            (True, '', '', True, '', ''),
            (True, '', '', False, '', ''),
        ]
        rules.load_rules(some_rules)
        res = rules.apply_until_predicate_fails()
        assert_expected(res, None)

        some_rules = [
            (True, '', '', True, '', ''),
            (False, '', '', False, '', ''),
        ]
        rules.load_rules(some_rules)
        res = rules.apply_until_predicate_fails()
        assert_expected(res, False)

        some_rules = [
            (True, '', '', True, '', ''),
            (False, '', '', True, '', ''),
        ]
        rules.load_rules(some_rules)
        res = rules.apply_until_predicate_fails()
        assert_expected(res, False)

        assert_expected(quit_check_mock.call_count, 9)

    def test_is_not_null_predicate(self):
        ok_(
            transform_rules.is_not_null_predicate(
                {'alpha': 'hello'}, None, None, None, 'alpha'
            )
        )
        ok_(not
            transform_rules.is_not_null_predicate(
                {'alpha': 'hello'}, None, None, None, 'beta'
            )
        )
        ok_(not
            transform_rules.is_not_null_predicate(
                {'alpha': ''}, None, None, None, 'alpha'
            )
        )
        ok_(not
            transform_rules.is_not_null_predicate(
                {'alpha': None}, None, None, None, 'alpha'
            )
        )

    def test_rule_simple(self):
        fake_config = DotDict()
        fake_config.logger = Mock()
        fake_config.chatty_rules = False
        fake_config.chatty = False

        r1 = transform_rules.Rule(fake_config)
        eq_(r1.predicate(None, None, None, None), True)
        eq_(r1.action(None, None, None, None), True)
        eq_(r1.act(), (True, True))

        class BadPredicate(transform_rules.Rule):
            def _predicate(self, *args, **kwargs):
                return False

        r2 = BadPredicate(fake_config)
        eq_(r2.predicate(None, None, None, None), False)
        eq_(r2.action(None, None, None, None), True)
        eq_(r2.act(), (False, None))

        class BadAction(transform_rules.Rule):
            def _action(self, *args, **kwargs):
                return False

        r3 = BadAction(fake_config)
        eq_(r3.predicate(None, None, None, None), True)
        eq_(r3.action(None, None, None, None), False)
        eq_(r3.act(), (True, False))

    def test_rule_exceptions(self):
        fake_config = DotDict()
        fake_config.logger = Mock()
        fake_config.chatty_rules = False
        fake_config.chatty = False

        class BadPredicate(transform_rules.Rule):
            def _predicate(self, *args, **kwargs):
                raise Exception("highwater")

        r2 = BadPredicate(fake_config)
        ok_(not fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        eq_(r2.predicate(None, None, None, None), False)
        ok_(fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        eq_(r2.action(None, None, None, None), True)
        ok_(not fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        eq_(r2.act(), (False, None))
        ok_(fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        class BadAction(transform_rules.Rule):
            def _action(self, *args, **kwargs):
                raise Exception("highwater")

        r3 = BadAction(fake_config)
        ok_(not fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        eq_(r3.predicate(None, None, None, None), True)
        ok_(not fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        eq_(r3.action(None, None, None, None), False)
        ok_(fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

        eq_(r3.act(), (True, False))
        ok_(fake_config.logger.debug.called)
        fake_config.logger.debug.reset_mock()

    def test_rules_in_config(self):
        config = DotDict()
        config.chatty_rules = False
        config.chatty = False
        config.tag = 'test.rule'
        config.action = 'apply_all_rules'
        config['TestRuleTestLaughable.laughable'] = 'wilma'
        config['TestRuleTestDangerous.dangerous'] = 'dwight'
        config.rules_list = DotDict()
        config.rules_list.class_list = [
            (
                'TestRuleTestLaughable',
                TestRuleTestLaughable,
                'TestRuleTestLaughable'
            ),
            (
                'TestRuleTestDangerous',
                TestRuleTestDangerous,
                'TestRuleTestDangerous'
            )
        ]
        trs = transform_rules.TransformRuleSystem(config)

        ok_(isinstance(trs.rules[0], TestRuleTestLaughable))
        ok_(isinstance(trs.rules[1], TestRuleTestDangerous))
        ok_(trs.rules[0].predicate(None))
        ok_(trs.rules[1].action(None))
