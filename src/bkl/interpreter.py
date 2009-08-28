#
#  This file is part of Bakefile (http://www.bakefile.org)
#
#  Copyright (C) 2008-2009 Vaclav Slavik
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#  IN THE SOFTWARE.
#

import api
import expr
import model
from parser.ast import *
from error import Error, ParserError

class Interpreter(object):
    """
    Interpreter processes parsed AST and constructs a project model from it.

    It doesn't do anything smart like optimizing things, it does only the
    minimal processing needed to produce a valid, albeit suboptimal, model.
    This includes checking variables scopes and type correctness etc.

    .. attribute:: context

       Current context. This is the inner-most :class:`bkl.model.ModelPart`
       at the time of parsing. Initially, it is set to a new
       :class:`bkl.model.Module` instance by :meth:`create_model`. When
       descending into a target, it is temporarily set to said target and
       then restored and so on.
    """

    def __init__(self, ast):
        """Constructor creates interpreter for given AST."""
        self.ast = ast
        self._ast_dispatch = {
            AssignmentNode : self.on_assignment,
            TargetNode     : self.on_target,
            NilNode        : lambda x: x, # do nothing
        }


    def create_model(self):
        """Returns constructed model, as :class:`bkl.model.Project` instance."""
        self.model = model.Project()
        self.context = model.Module()
        self.model.modules.append(self.context)

        self.handle_children(self.ast.children, self.context)

        return self.model


    def handle_children(self, children, context):
        """
        Runs model creation of all children nodes.

        :param children: List of AST nodes to treat as children.
        :param context:  Context (aka "local scope"). Interpreter's
               :attr:`context` is set to it for the duration of the call.
        """
        try:
            old_ctxt = self.context
            self.context = context
            for n in children:
                self._handle_node(n)
        finally:
            self.context = old_ctxt


    def _handle_node(self, node):
        func = self._ast_dispatch[type(node)]
        func(node)


    def on_assignment(self, node):
        varname = node.var.text
        value = self._build_assigned_value(node.value)

        var = self.context.get_variable(varname)
        if var is None:
            # create new variable
            var = model.Variable(varname, value)
            self.context.add_variable(var)
        else:
            # modify existing variable
            if var.readonly:
                raise Error(node.pos, "variable \"%s\" is read-only" % varname)
            var.set_value(value)


    def on_target(self, node):
        name = node.name.text
        if name in self.context.targets:
            raise ParserError(node.pos, "target ID \"%s\" not unique" % name)

        type_name = node.type.text
        try:
            target_type = api.TargetType.get(type_name)
            target = model.Target(name, target_type)
            self.context.add_target(target)
        except KeyError:
            raise ParserError(node.pos, "unknown target type \"%s\"" % type_name)

        # handle target-specific variables assignments etc:
        self.handle_children(node.content, target)


    def _build_assigned_value(self, ast, result_type=None):
        """
        Build :class:`bkl.expr.Expr` from given AST node of
        AssignedValueNode type.

        If result_type is specified, then the expression will be of that
        type, or the function will throw an exception.
        """
        assert isinstance(ast, AssignedValueNode)
        values = ast.values
        if len(values) == 1:
            return self._build_expression(values[0], result_type)
        else:
            assert result_type==None # FIXME: handle nested type correctly
            items = [self._build_expression(e, result_type) for e in values]
            return expr.ListExpr(items)


    def _build_expression(self, ast, result_type=None):
        if isinstance(ast, ValueNode):
            # FIXME: type handling
            return expr.ConstExpr(ast.text)
        assert False, "unrecognized AST node"