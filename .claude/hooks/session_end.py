#!/usr/bin/env python3
"""
Session End Hook for Claude Code
Runs when a session ends.
"""

import sys
import json

def main():
    """Main hook entry point."""
    try:
        # Return success response
        print(json.dumps({
            'success': True,
            'message': 'Session end hook executed'
        }))
        return 0
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        return 1

if __name__ == '__main__':
    sys.exit(main())
