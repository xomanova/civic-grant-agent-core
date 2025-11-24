"""
Helpers
General utility functions
"""

def deep_update(source, overrides):
    """
    Recursively update the 'source' dictionary with values from 'overrides'.
    Does not delete existing keys in 'source' unless 'overrides' explicitly replaces them.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and value:
            # If the key exists in source and is a dict, recurse
            node = source.setdefault(key, {})
            if isinstance(node, dict):
                deep_update(node, value)
            else:
                # If source[key] was not a dict (e.g. a string), overwrite it
                source[key] = value
        else:
            # If value is not a dict (string, int, list), overwrite
            source[key] = value
    return source
