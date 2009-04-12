#
#  This file is part of Bakefile (http://www.bakefile.org)
#
#  Copyright (C) 2009 Vaclav Slavik
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

# Metaclass used for all extensions in order to implement automatic
# extensions registration. For internal use only.
class _ExtensionMetaclass(type):

    def __init__(cls, name, bases, dct):
        super(_ExtensionMetaclass, cls).__init__(name, bases, dct)

        assert len(bases) == 1, "multiple inheritance not supported"

        # skip base classes, only register implementations:
        if name == "Extension":
            return
        if cls.__base__ is Extension:
            # initialize list of implementations for direct extensions:
            cls.implementations = {}
            return

        # for "normal" implementations of extensions, find the extension
        # type class (we need to handle the case of deriving from an existing
        # extension):
        base = cls.__base__
        while not base.__base__ is Extension:
            base = base.__base__
        if cls.name in base.implementations:
            existing = base.implementations[cls.name]
            raise RuntimeError("conflicting implementations for %s \"%s\": %s.%s and %s.%s" %
                               (base.__name__,
                                cls.name,
                                cls.__module__, cls.__name__,
                                existing.__module__, existing.__name__))
        base.implementations[cls.name] = cls



class Extension(object):
    """
    Base class for all Bakefile extensions.

    .. attribute:: name

       Use-visible name of the extension. For example, the name for targets
       extensions is what is used in target declarations; likewise for
       property names.

    .. attribute:: implementations

       Dictionary of classes that implement this extension, keyed by their name.
    """

    __metaclass__ = _ExtensionMetaclass

    name = None
    implementations = {}
