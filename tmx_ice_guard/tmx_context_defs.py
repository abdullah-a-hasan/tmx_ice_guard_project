import hashlib
import zlib

#TMX platform definitions
tmx_context_defs = {}

# Phrase/Memsource
tmx_context_defs['transifix'] = {"prev_text_prop": "context",
                                 "context_level": "tu"
                                 }

tmx_context_defs['phrase'] = {"prev_text_prop": "context_prev",
                              "next_text_prop": "context_next",
                              "context_level": "tuv",
                              "remove_props": ["created_by", "modified_by"],
                              "file_prop": "filename",
                              "project_prop": "project",
                              }

tmx_context_defs['memoq'] = {"prev_text_prop": "x-context-pre",
                             "next_text_prop": "x-context-post",
                             "context_level": "tuv",
                             "remove_props": ["client", "domain", "subject", "corrected", "aligned", "x-Project", "x-Client", "x-Domain"],
                             "file_prop": "x-document",
                             "project_prop": "project"
                             }

# XTM
tmx_context_defs['xtm'] = {"prev_text_prop": "x-previous-source-text",
                           "next_text_prop": "x-next-source-text",
                           "prev_hash_prop": "x-previous-crc",
                           "next_hash_prop": "x-next-crc",
                           "remove_props": ["x-previous-target-text", "x-next-target-text", "x-previous-target-crc", "x-next-target-crc"],
                           "context_level": "tu",
                           "hash_func": lambda text: zlib.crc32(text.encode())
                           }

# GlobalLink/WordFast
tmx_context_defs['gl'] = {"prev_text_prop": "previousMd5Segment",
                          "next_text_prop": "nextMd5Segment",
                          "prev_hash_prop": "previousMd5Checksum",
                          "next_hash_prop": "nextMd5Checksum",
                          "context_level": "tu",
                          "hash_func": lambda text: hashlib.md5(text.lower().encode()).hexdigest()
                          }

# Trados
tmx_context_defs['trados'] = {"prev_text_prop": "x-ContextContent",
                              "remove_props": ["x-Context", "x-Origin", "x-ConfirmationLevel", "x-StructureContext:MultipleString", "x-LastUsedBy", "x-ContextContent",
                                               "x-OriginalFormat"],
                              "context_level": "tu"
                              #"replacements": [(r' \| .+$', '')],
                              }
