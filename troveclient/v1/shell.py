from __future__ import print_function

import argparse
import copy
import os
import sys
import time

from troveclient import exceptions
from troveclient import utils


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print("\nFinished")
            break
        elif status == "error":
            print("\nError %(action)s instance" % {'action': action})
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _print_instance(instance):
    utils.print_dict(instance._info)


def _find_instance(cs, instance):
    """Get a instance by ID."""
    return utils.find_resource(cs.instances, instance)


@utils.service_type('database')
def do_list(cs, args):
    """List all the instances."""
    return "list_instances"


@utils.arg('instance', metavar='<instance>', help='ID of the instance.')
@utils.service_type('database')
def do_show(cs, args):
    """Show details about a instance."""
    instance = _find_instance(cs, args.instance)
    _print_instance(instance)
