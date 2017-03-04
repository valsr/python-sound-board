"""
Created on Mar 3, 2017

@author: valsr <valsr@valsr.com>
"""
import unittest
from com.valsr.type.tree import GenericTreeNode


class TestGenericTreeNode(unittest.TestCase):

    def setUp(self):
        self.node = GenericTreeNode()

    def test_id(self):
        self.assertIsNotNone(self.node.id)

    def test_setting_data(self):
        self.node.foo = '1'
        self.assertEqual(self.node._data['foo'], '1')

        self.node.foo = 'data'
        self.assertEqual(self.node._data['foo'], 'data')

    def test_getting_data(self):
        self.node.foo = "1"
        self.assertEqual(self.node.foo, "1")

    def test_has(self):
        self.node.foo = "1"
        self.assertTrue(self.node.has_data('foo'))
        self.assertFalse(self.node.has_data('bar'))

    def test_get_non_existing_data(self):
        self.node.foo = "1"
        self.assertRaises(AttributeError, lambda: self.node.bar)

    def test_get_data(self):
        self.assertDictEqual(self.node.get_data(), {})
        self.node.foo = "1"

        self.assertDictEqual(self.node.get_data(), {"foo": "1"})

    def test_set_data(self):
        d = {"foo": "1", "bar": 12.5}
        self.assertDictEqual(self.node.get_data(), {})

        self.node.set_data(d)
        self.assertEqual(self.node.foo, "1")
        self.assertEqual(self.node.bar, 12.5)

    def test_set_data_none(self):
        self.assertDictEqual(self.node.get_data(), {})

        self.node.set_data(None)
        self.assertDictEqual(self.node.get_data(), {})

    def test_set_data_except(self):
        self.assertRaises(TypeError, self.node.set_data, 1)

    def test_clear_data(self):
        self.assertDictEqual(self.node.get_data(), {})
        self.node.foo = "1"

        self.assertDictEqual(self.node.get_data(), {"foo": "1"})
        self.node.clear_data()
        self.assertDictEqual(self.node.get_data(), {})

    def test_add_node(self):
        self.assertIsInstance(self.node.add_node(GenericTreeNode(label="1")), GenericTreeNode)
        self.assertEqual(len(self.node.children()), 1)

        self.assertIsInstance(self.node.add_node(GenericTreeNode(label="2")), GenericTreeNode)
        self.assertEqual(len(self.node.children()), 2)

        n = GenericTreeNode(label="3")
        self.assertIsNone(n.parent())
        self.assertIsInstance(self.node.add_node(n), GenericTreeNode)
        self.assertIs(self.node, n.parent())
        self.assertEqual(len(self.node.children()), 3)

    def test_add_node_appending(self):
        self.node.add_node(GenericTreeNode(label="1"))
        self.node.add_node(GenericTreeNode(label="2"))
        self.node.add_node(GenericTreeNode(label="3"))
        self.assertEqual(self.node.children()[0].label, "1")
        self.assertEqual(self.node.children()[1].label, "2")
        self.assertEqual(self.node.children()[2].label, "3")

    def test_add_node_position(self):
        self.assertIsInstance(self.node.add_node(GenericTreeNode(label="1")), GenericTreeNode)
        self.assertEqual(len(self.node.children()), 1)

    def test_add_node_type(self):
        self.assertRaises(TypeError, self.node.add_node, 1)

    def test_add_node_none(self):
        self.assertRaises(TypeError, self.node.add_node, node=None)
        self.assertEqual(len(self.node.children()), 0)

    def set_up_tree(self):
        t = GenericTreeNode()
        labels = ['first', 'second', 'third', 'forth', 'last']

        for l1 in labels:
            n1 = GenericTreeNode(label=l1)
            t.add_node(n1)

            for l2 in labels:
                n2 = GenericTreeNode(label=l2)
                n1.add_node(n2)

                for l3 in labels:
                    n2.add_node(GenericTreeNode(label=l3))

        return t

    def test_node_at_default(self):
        t = self.set_up_tree()

        self.assertEqual(t.node_at().label, "first")

    def test_node_at_pos(self):
        t = self.set_up_tree()

        self.assertEqual(t.node_at(0).label, "first")
        self.assertEqual(t.node_at(1).label, "second")
        self.assertEqual(t.node_at(3).label, "forth")
        self.assertEqual(t.node_at(4).label, "last")

    def test_node_at_past_last(self):
        t = self.set_up_tree()

        self.assertEqual(t.node_at(5), None)

    def test_node_at_neg_pos(self):
        t = self.set_up_tree()

        self.assertEqual(t.node_at(-1).label, "last")
        self.assertEqual(t.node_at(-2).label, "forth")
        self.assertEqual(t.node_at(-4).label, "second")

    def test_node_at_neg_past_last(self):
        t = self.set_up_tree()

        self.assertEqual(t.node_at(-6), None)

    def test_clear_nodes(self):
        t = self.set_up_tree()

        n = t.node_at()
        self.assertNotEqual(len(t.children()), 0)
        self.assertIs(t.clear_nodes(), t)
        self.assertEqual(len(t.children()), 0)
        self.assertIsNone(n.parent())

    def test_children(self):
        t = self.set_up_tree()
        c = t.children()
        self.assertIsNotNone(c)
        self.assertEqual(c[0].label, "first")
        self.assertIs(c[0], t.node_at())

    def test_parent(self):
        n = GenericTreeNode()
        self.assertIsNone(n.parent())

        self.node.add_node(n)
        self.assertIs(n.parent(), self.node)

    def test_remove_node_none(self):
        t = self.set_up_tree()

        n = t.remove_at()
        self.assertIsNotNone(n)
        self.assertEqual(n.label, 'last')

    def test_remove_node(self):
        t = self.set_up_tree()

        n = t.remove_at(0)
        self.assertIsNotNone(n)
        self.assertEqual(n.label, 'first')

        n = t.remove_at(1)
        self.assertIsNotNone(n)
        self.assertEqual(n.label, 'third')

    def test_remove_node_past_last(self):
        t = self.set_up_tree()

        n = t.remove_at(10)
        self.assertIsNone(n)

    def test_remove_node_neg(self):
        t = self.set_up_tree()

        n = t.remove_at(-1)
        self.assertIsNotNone(n)
        self.assertEqual(n.label, 'last')

        n = t.remove_at(-2)
        self.assertIsNotNone(n)
        self.assertEqual(n.label, 'third')

    def test_remove_node_neg_past_len(self):
        t = self.set_up_tree()

        n = t.remove_at(10)
        self.assertIsNone(n)

    def test_remove_node_node(self):
        t = self.set_up_tree()

        n = t.node_at(0)

        children_size = len(t.children())
        self.assertIs(t.remove_node(n), t)
        self.assertIsNot(t.node_at(0), n)
        self.assertEqual(len(t.children()), children_size - 1)

    def test_remove_node_id(self):
        t = self.set_up_tree()

        n = t.node_at(0)

        children_size = len(t.children())
        self.assertIs(t.remove_node_by_id(n.id), n)
        self.assertIsNot(t.node_at(0), n)
        self.assertEqual(len(t.children()), children_size - 1)

        # remove non existing
        self.assertIsNone(t.remove_node_by_id(n.node_at(1).id))

    def test_remove_child_node_id(self):
        t = self.set_up_tree()

        n = t.node_at(1).node_at(1)

        self.assertIsNone(t.remove_node_by_id(n.id))
        self.assertIs(t.remove_node_by_id(n.id, True), n)
        self.assertIsNone(t.get_node(n.id, True))

    def test_iterate(self):
        t = self.set_up_tree()
        nodes = [x for x in t.iterate_nodes(lambda n: n.label == "first")]
        self.assertEqual(len(nodes), 1)

        nodes = [x for x in t.iterate_nodes(lambda n: n.label == "nonexisting")]
        self.assertEqual(len(nodes), 0)

    def test_iterate_all(self):
        t = self.set_up_tree()
        nodes = [x for x in t.iterate_nodes(lambda n: n.label == "first", True)]
        self.assertEqual(len(nodes), 31)

        nodes = [x for x in t.iterate_nodes(lambda n: n.label == "nonexisting", True)]
        self.assertEqual(len(nodes), 0)

    def test_iterate_default(self):
        t = self.set_up_tree()
        nodes = [x for x in t.iterate_nodes()]
        self.assertEqual(len(nodes), 5)

        nodes = [x for x in t.iterate_nodes(descend=True)]
        self.assertEqual(len(nodes), 155)

    def test_get_node(self):
        t = self.set_up_tree()

        n = t.node_at(3)
        self.assertEqual(t.get_node(n.id), n)

    def test_get_node_non_existing(self):
        t = self.set_up_tree()

        self.assertIsNone(t.get_node(1))
        self.assertIsNone(t.get_node(t.node_at(2).node_at(2).id))

    def test_get_child_node(self):
        t = self.set_up_tree()

        self.assertIsNone(t.get_node(1))
        self.assertIsNotNone(t.get_node(t.node_at(2).node_at(2).id, True))

    def test_prevent_duplicate_add(self):
        n = GenericTreeNode()
        self.node.add_node(n)

        self.assertRaises(RuntimeError, self.node.add_node, n)
        self.node.add_node(GenericTreeNode())
        self.assertRaises(RuntimeError, self.node.add_node, n)

    def test_prevent_self_add(self):
        self.assertRaises(RuntimeError, self.node.add_node, self.node)

    def test_prevent_recursive_add(self):
        n = GenericTreeNode()

        self.node.add_node(GenericTreeNode())
        self.node.add_node(n)
        self.assertRaises(RuntimeError, n.add_node, self.node)

    def test_prevent_add_attached_node(self):
        n = GenericTreeNode()
        t = GenericTreeNode()
        self.node.add_node(n)

        self.assertRaises(RuntimeError, t.add_node, n)
        n.detach()
        t.add_node(n)

    def test_detach(self):
        n = GenericTreeNode()
        self.assertIsNone(n.parent())

        self.node.add_node(n)
        self.assertIs(n.parent(), self.node)

        n.detach()
        self.assertIsNone(n.parent())
        self.assertEqual(len(self.node.children()), 0)
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
