import json


def to_camel_case(text):
    s = ''.join(x for x in text.replace("_", " ").title() if not x.isspace())
    return s[:1].lower() + s[1:]


class Serializable(object):
    def to_json(self):
        return json.dumps(self, default=lambda x: x.__dict__,
                          sort_keys=True, indent=4)


class AppleSerializable(object):
    def to_json(self):
        def make_apple_api_compliant(obj):
            new_dict = {}
            dict_repr = obj.__dict__
            for key, val in dict_repr.items():
                if key == '_Keyword__text':
                    key = ' text'
                    val = dict_repr['_Keyword__updated_text'] if \
                        dict_repr['_Keyword__updated_text'] is not None else \
                        dict_repr['_Keyword__text']
                if key == '_Keyword__updated_text':
                    continue
                if key.startswith("_"):
                    new_key = to_camel_case(key[1:])
                else:
                    new_key = to_camel_case(key)
                new_dict[new_key] = val
            return new_dict

        return json.dumps(self, default=make_apple_api_compliant,
                          sort_keys=True, indent=4)


class Synchronizable(object):
    def set_sync_manager(self, sync_manager):
        self.sync_manager = sync_manager

    def synchronize(self, save_callback=lambda x: x, *args, **kwargs):
        if self.sync_manager is not None:
            save_callback(self.to_json())
            self.sync_manager.pending_actions.append(
                (self.__class__.__name__, self.to_json(), args[1:], kwargs)
            )
            return False
        return True
