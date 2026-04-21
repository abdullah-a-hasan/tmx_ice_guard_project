import xml.etree.ElementTree as ET
import xml.dom.minidom
from tmx_ice_guard.tmx_context_defs import tmx_context_defs
from tmx_ice_guard.helpers import pre_process_context, post_process_context
import copy
import re
import base64


class ICEGuard:

    @staticmethod
    def _pretty_print_tu_except_seg(xml_string, clean_empty_lines=False):
        """
        Protects <seg> tags from being reformatted by minidom by encoding them because <seg> need to be left untouched.
        :param xml_string: The XML string of the entire <TU> element.
        :param clean_empty_lines:
        :return:
        """

        def base64_enc_match(match):
            matched_text = match.group(0)
            return base64.b64encode(matched_text.encode("utf-8")).decode()

        def base64_dec_match(match):
            matched_text = match.group(0)
            return base64.b64decode(matched_text.encode("utf-8")).decode()

        seg_pattern = r'(?<=<seg>).*?(?=</seg>)'
        formatted = re.sub(seg_pattern, base64_enc_match, xml_string.decode('utf-8'))  # encode seg contents
        tu_elem = ET.fromstring(formatted)
        ET.indent(tu_elem, "   ", 0)
        formatted = "\n" + ET.tostring(tu_elem, encoding='unicode')
        formatted = re.sub(seg_pattern, base64_dec_match, formatted)  # decode seg contents
        formatted = re.sub("\n+", "\n", formatted)
        return formatted.encode()


    @staticmethod
    def _find_parent(root, child):
        if child is None:
            return None
        for parent in root.iter():
            if child in list(parent):
                return parent
        return None

    @staticmethod
    def _remove_child(root, child):
        parent = ICEGuard._find_parent(root, child)
        if parent is not None:
            parent.remove(child)

    @staticmethod
    def _detect_tmx_flavor(header_elem):
        creation_tool = header_elem.attrib.get('creationtool', '')
        if creation_tool.lower().startswith("sdl"):  #SDL Language Platform
            return "trados"
        if creation_tool.lower().startswith("memsource"):  #memsource_tool
            return "phrase"
        if creation_tool.lower().startswith("memoq"):  #MemoQ
            return "memoq"
        if creation_tool.lower() == "TDC Analysis Package".lower():  #TDC Analysis Package
            return "gl"  #GlobalLink
        if creation_tool.lower() == "com.xmlintl.tm.db.tmx.writers.TMXStaxWriter".lower():
            return "xtm"
        if creation_tool.lower().startswith("transifex"): #Transifex.com
            return "transifex"
        else:
            return "Unknown"

    @staticmethod
    def convert(in_file: str, out_file: str, source_platform: str, target_platform: str, pretty=False):
        counter = 0
        # Open the input XML file and output file
        with open(out_file, 'wb') as output_file:
            output_file.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            # Iterate through the XML elements
            for event, elem in ET.iterparse(in_file, events=('start', 'end')):
                if elem.tag == 'tmx':
                    if event == 'start':
                        output_file.write(f'<tmx version=\"{elem.attrib['version']}\">\n'.encode('utf-8'))
                    if event == 'end':
                        output_file.write(b'\n</tmx>')
                    elem.clear()
                    continue
                if elem.tag == 'body':
                    if event == 'start':
                        output_file.write(b'\n<body>\n')
                    if event == 'end':
                        output_file.write(b'\n</body>\n')
                    elem.clear()
                    continue
                if event == 'start' and elem.tag == 'header':
                    # Get tool name from header, if auto, and load settings tool settings from tmx_context_defs
                    if source_platform == "auto":
                        source_platform = ICEGuard._detect_tmx_flavor(elem)
                        yield {"type": "flavor", "platform": source_platform}
                    if source_platform not in tmx_context_defs.keys() or target_platform not in tmx_context_defs.keys():
                        raise ValueError(f"Invalid source and/or target platform. Must be one of: " + ", ".join(tmx_context_defs.keys()))
                    input_prev_prop = tmx_context_defs[source_platform].get('prev_text_prop')
                    input_next_prop = tmx_context_defs[source_platform].get('next_text_prop')
                    input_hash_prev_prop = tmx_context_defs[source_platform].get('prev_hash_prop')
                    input_hash_next_prop = tmx_context_defs[source_platform].get('next_hash_prop')
                    input_context_level = tmx_context_defs[source_platform].get("context_level", 'tu')
                    remove_props = tmx_context_defs[source_platform].get('remove_props')

                    output_prev_prop = tmx_context_defs[target_platform].get('prev_text_prop')
                    output_next_prop = tmx_context_defs[target_platform].get('next_text_prop')
                    output_hash_prev_prop = tmx_context_defs[target_platform].get('prev_hash_prop')
                    output_hash_next_prop = tmx_context_defs[target_platform].get('next_hash_prop')
                    output_context_level = tmx_context_defs[target_platform].get("context_level", 'tu')
                    hash_func = tmx_context_defs[target_platform].get('hash_func')
                    output_file.write(ET.tostring(elem, encoding='utf-8'))
                    elem.clear()
                    continue
                if event == 'start' and elem.tag == 'tu':
                    counter += 1
                    if counter % 1000 == 0:
                        yield {"type": "tu_progress", "count": counter}

                    # Process and rename next context props
                    if input_next_prop and output_next_prop:
                        next_source_elem = elem.find(f'.//prop[@type="{input_next_prop}"]')
                        if next_source_elem is not None:
                            if next_source_elem.text:
                                next_source_elem.text = pre_process_context(source_platform, next_source_elem.text)
                                next_source_elem.text = post_process_context(target_platform, next_source_elem.text)
                            # Rename type of context prop
                            next_source_elem.attrib['type'] = output_next_prop
                            # Move context prop to the desired level "tu" vs. "tuv", if input_context_level != output_context_level
                            if input_context_level != output_context_level:
                                #print(f"Moving context prop to {output_context_level} level")
                                copied_next_elem = copy.deepcopy(next_source_elem)
                                ICEGuard._remove_child(elem, next_source_elem)
                                if output_context_level == 'tu':
                                    elem.insert(0, copied_next_elem)
                                elif output_context_level == 'tuv':
                                    target_elem = elem.find('tuv')
                                    if target_elem is not None:
                                        target_elem.insert(0, copied_next_elem)
                            if hash_func and output_hash_next_prop and next_source_elem.text is not None:
                                next_hash_elem = ET.Element('prop', type=output_hash_next_prop)
                                next_hash_elem.text = str(hash_func(next_source_elem.text))
                                if output_context_level == 'tu':
                                    elem.insert(0, next_hash_elem)
                                elif output_context_level == 'tuv':
                                    target_elem = elem.find('tuv')
                                    if target_elem is not None:
                                        target_elem.insert(0, next_hash_elem)

                    # Process and rename prev context props
                    if input_prev_prop and output_prev_prop:
                        prev_source_elem = elem.find(f'.//prop[@type="{input_prev_prop}"]')
                        if prev_source_elem is not None:
                            if prev_source_elem.text:
                                prev_source_elem.text = pre_process_context(source_platform,
                                                                            prev_source_elem.text)  # multi_regex_replace(prev_source_elem.text, input_replacements)
                                prev_source_elem.text = post_process_context(target_platform,
                                                                             prev_source_elem.text)  # multi_regex_replace(prev_source_elem.text, input_replacements)
                            # Rename type of context prop
                            prev_source_elem.attrib['type'] = output_prev_prop
                            # Move context prop to the desired level "tu" vs. "tuv", if input_context_level != output_context_level
                            if input_context_level != output_context_level:
                                #print(f"Moving context prop to {output_context_level} level")
                                copied_prev_elem = copy.deepcopy(prev_source_elem)
                                ICEGuard._remove_child(elem, prev_source_elem)
                                if output_context_level == 'tu':
                                    elem.insert(0, copied_prev_elem)
                                elif output_context_level == 'tuv':
                                    target_elem = elem.find('tuv')
                                    if target_elem is not None:
                                        target_elem.insert(0, copied_prev_elem)
                            if hash_func and output_hash_prev_prop and prev_source_elem.text is not None:
                                prev_hash_elem = ET.Element('prop', type=output_hash_prev_prop)
                                prev_hash_elem.text = str(hash_func(prev_source_elem.text))
                                if output_context_level == 'tu':
                                    elem.insert(0, prev_hash_elem)
                                elif output_context_level == 'tuv':
                                    target_elem = elem.find('tuv')
                                    if target_elem is not None:
                                        target_elem.insert(0, prev_hash_elem)

                    # Clean up input hash props
                    if input_hash_prev_prop:
                        prev_hash_elem = elem.find(f'.//prop[@type="{input_hash_prev_prop}"]')
                        ICEGuard._remove_child(elem, prev_hash_elem)

                    if input_hash_next_prop:
                        next_hash_elem = elem.find(f'.//prop[@type="{input_hash_next_prop}"]')
                        ICEGuard._remove_child(elem, next_hash_elem)

                    # remove unwanted props
                    if remove_props:
                        for unwanted_prop in remove_props:
                            unwanted_elems = elem.findall(f'.//prop[@type="{unwanted_prop}"]')
                            for unwanted_elem in unwanted_elems:
                                ICEGuard._remove_child(elem, unwanted_elem)
                    #ugly
                    if not pretty:
                        output_file.write(ET.tostring(elem, encoding='UTF-8'))
                    #pretty
                    else:
                        output_file.write(ICEGuard._pretty_print_tu_except_seg(ET.tostring(elem, encoding='UTF-8'), clean_empty_lines=True))
                    elem.clear()
        yield {"type": "done", "count": counter, "source_platform": source_platform, "target_platform": target_platform}


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("This is not a standalone script.")
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
