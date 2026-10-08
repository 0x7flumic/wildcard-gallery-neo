from modules.ui_extra_networks import ExtraNetworksPage, ExtraNetworksItem, quote_js, register_page
from modules import script_callbacks
import modules.scripts as scripts 
import zlib

from utils.wildcard_manager import wildcard_manager
from utils.wildcard_common import (
    collect_gallery_cards,
    clean_residue,
    get_safe_name_2,
    collect_previews, delete_previews, 
    WILDCARDS_FOLDER,
    CARDS_FOLDER,
    RES_FOLDER,
    WILD_STR,
)
from utils.wildcard_preview import (
    txt2img_process
)
import os
import html
import gradio as gr
from modules import shared

addon_name = "Wildcard Gallery Neo"
extra_network_name = "Wildcard Gallery Neo"

log_suffix = "[Wildcard Gallery Neo] "
error_suffix = "[Wildcard Gallery Neo ERR] "

def collect_wildcard_branches():
    wild_paths = collect_gallery_cards(WILDCARDS_FOLDER)
    branches = set()
    for wpath in wild_paths:
        parts = wpath.split('/')
        for i in range(1, len(parts)):
            branches.add('/'.join(parts[:i]))
    return sorted(list(branches), key=shared.natural_sort_key)


class WildcardGalleryCards(ExtraNetworksPage):

    def __init__(self):
        super().__init__(extra_network_name)
        self.allow_negative_prompt = True
        self.cards: list[str] = []
        self.subdirs: list[str] = []

        if not os.path.exists(CARDS_FOLDER):
            os.makedirs(CARDS_FOLDER, exist_ok=True)

        self.refresh()

    def refresh(self):
        wildcard_manager.refresh_wildcards()
        from utils.wildcard_common import invalidate_cards_cache
        invalidate_cards_cache()
        
        self.cards = collect_gallery_cards(WILDCARDS_FOLDER)
        
        # Precompute subdirectories once per refresh
        subdirs = set()
        for wild_path in self.cards:
            parts = wild_path.split("/")
            for i in range(1, len(parts)):
                subdirs.add("/".join(parts[:i]) + "/")
        self.subdirs = sorted(list(subdirs), key=shared.natural_sort_key)
        
        clean_residue(CARDS_FOLDER)


    def create_item(self, wild_path: str, index=1, enable_filter=True):
        leaf_name, category = get_safe_name_2(wild_path, self.cards)
        display_name = leaf_name.replace("_", " ").upper()
        
        # Virtual file path without touching disk
        virtual_file_base = os.path.abspath(os.path.join(CARDS_FOLDER, wild_path.replace("/", os.path.sep)))
        
        prompt = f"__{wild_path}__"
        card_id = f"wildcard-gallery-neo:{wild_path}".encode("utf-8")

        return {
            "name": wild_path,
            "filename": virtual_file_base,
            "shorthash": f"{zlib.adler32(card_id) & 0xffffffff:08x}",
            "preview": self.find_preview(virtual_file_base),
            "description": self.find_description(virtual_file_base),
            "search_terms": [wild_path, display_name, leaf_name, category, self.search_terms_from_path(virtual_file_base)],
            "prompt": quote_js(prompt),
            "local_preview": f"{virtual_file_base}.jpeg",
            "sort_keys": {
                "default": f"{category.lower()}-{display_name.lower()}",
                "date_created": index,
                "date_modified": f"{category.lower()}-{index}",
                "name": wild_path.lower(),
            },
        }

    def list_items(self):
        i = 0

        for FILE in self.cards:
            i += 1
            yield self.create_item(FILE, i)

    def find_preview(self, path):
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            return None
        return super().find_preview(path)

    def find_description(self, path):
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            return None
        return super().find_description(path)

    def read_user_metadata(self, item, use_cache=True):
        filename = item.get("filename", None)
        if filename:
            dirname = os.path.dirname(filename)
            if not os.path.isdir(dirname):
                item["user_metadata"] = {}
                return
        super().read_user_metadata(item, use_cache=use_cache)

    def allowed_directories_for_previews(self):
        return [CARDS_FOLDER]

    def create_tree_file_item_html(self, tabname: str, file_path: str, item: dict) -> str:
        item_html_args = self.create_item_html(tabname, item)
        action_buttons = "".join(
            [
                item_html_args["copy_path_button"],
                item_html_args["metadata_button"],
                item_html_args["edit_button"],
            ]
        )
        action_buttons = f'<div class="button-row">{action_buttons}</div>'
        leaf_name = os.path.basename(file_path).replace("_", " ").upper()
        btn = self.btn_tree_tpl.format(
            **{
                "search_terms": "",
                "subclass": "tree-list-content-file",
                "tabname": tabname,
                "extra_networks_tabname": self.extra_networks_tabname,
                "onclick_extra": item_html_args["card_clicked"],
                "data_path": file_path,
                "data_hash": item["shorthash"],
                "action_list_item_action_leading": "<i class='tree-list-item-action-chevron'></i>",
                "action_list_item_visual_leading": "🗎",
                "action_list_item_label": leaf_name,
                "action_list_item_visual_trailing": "",
                "action_list_item_action_trailing": action_buttons,
            }
        )
        return f"<li class='tree-list-item tree-list-item--subitem' data-tree-entry-type='file'>{btn}</li>"

    def create_tree_view_html(self, tabname: str) -> str:
        """
        Builds the tree navigation sidebar from logical wildcard paths in memory
        instead of requiring physical dummy folders and files on disk.
        """
        nested_tree = {}
        for item in self.items.values():
            filename = item.get("filename", "")
            # Determine relative path from CARDS_FOLDER
            try:
                rel = os.path.relpath(filename, CARDS_FOLDER)
            except ValueError:
                rel = os.path.basename(filename)

            parts = rel.replace("\\", "/").split("/")
            curr = nested_tree
            for p in parts[:-1]:
                curr = curr.setdefault(p, {})
            curr[parts[-1]] = ExtraNetworksItem(item)

        if not nested_tree:
            return ""

        def _build_tree(data: dict, current_dir: str = ""):
            if not data:
                return None
            _dir_li = []
            _file_li = []
            for k, v in sorted(data.items(), key=lambda x: shared.natural_sort_key(x[0])):
                sub_path = f"{current_dir}/{k}" if current_dir else k
                if isinstance(v, ExtraNetworksItem):
                    _file_li.append(self.create_tree_file_item_html(tabname, sub_path, v.item))
                else:
                    sub_content = _build_tree(v, sub_path)
                    dir_html = self.create_tree_dir_item_html(tabname, sub_path, sub_content)
                    if dir_html:
                        _dir_li.append(dir_html)
            return "".join(_dir_li) + "".join(_file_li)

        res = _build_tree(nested_tree)
        return f"<ul class='tree-list tree-list--tree'>{res}</ul>" if res else ""

    def create_dirs_view_html(self, tabname: str) -> str:
        """
        Builds the folder buttons view from in-memory wildcard categories.
        """
        all_dirs = [""] + (self.subdirs or [])

        subdirs_html = "".join([f"""
        <button class='lg secondary gradio-button custom-button{" search-all" if subdir == "" else ""}' onclick='extraNetworksSearchButton("{tabname}", "{self.extra_networks_tabname}", event)'>
        {html.escape(subdir if subdir != "" else "all")}
        </button>
        """ for subdir in all_dirs])

        return subdirs_html


def btn_count_wildcards (use_wild_path, selected_wildcard, selected_wild_path):
    msg = error_suffix+"No wildcards selected"
    selected_wildcards_list  = selection_sequence (use_wild_path, selected_wildcard, selected_wild_path)
    if(selected_wildcards_list):
        msg = f"Parameters are selecting { len(selected_wildcards_list) } wildcards"
    
    return (gr.update(value= log_suffix + msg))

def btn_collect_previews (use_wild_path, selected_wildcard, selected_wild_path):
    msg = error_suffix+"No wildcards selected"
    selected_wildcards_list  = selection_sequence (use_wild_path, selected_wildcard, selected_wild_path)
    
    if(selected_wildcards_list):
        msg=""
        msg = msg + collect_previews(wildpath_selector= selected_wildcards_list) +"\n"
    
    return (gr.update(value= log_suffix+msg))

def btn_delete_previews (use_wild_path, selected_wildcard, selected_wild_path):
    msg = error_suffix+"No wildcards selected"
    selected_wildcards_list  = selection_sequence (use_wild_path, selected_wildcard, selected_wild_path)
    
    if(selected_wildcards_list):
        msg=""
        msg =  log_suffix + delete_previews(wildpath_selector= selected_wildcards_list)+"\n"+ msg 
    return (gr.update(value= msg))

def btn_optimize_previews():
    from PIL import Image
    from utils.wildcard_preview import resize_as_thumbnail
    optimized_count = 0
    skipped_count = 0
    
    image_files = []
    for root, dirs, files in os.walk(CARDS_FOLDER):
        for file in files:
            if file.lower().endswith((".jpeg", ".jpg", ".png", ".webp")):
                image_files.append(os.path.join(root, file))
                
    total_files = len(image_files)
    if total_files == 0:
        yield gr.update(value=log_suffix + "No preview images found to optimize.")
        return

    yield gr.update(value=log_suffix + f"Scanning previews... 0% (0/{total_files})")
    
    for idx, file_path in enumerate(image_files):
        try:
            with Image.open(file_path) as img:
                if img.width > 512 or img.height > 512:
                    resized_img = resize_as_thumbnail(img, 512)
                    img.close()
                    resized_img.save(file_path, quality=85)
                    optimized_count += 1
                else:
                    skipped_count += 1
        except Exception as e:
            print(f"[Wildcard Gallery Neo Error] Failed to optimize preview {file_path}: {e}")
            
        if (idx + 1) % max(1, total_files // 20) == 0 or (idx + 1) == total_files:
            percent = int((idx + 1) / total_files * 100)
            yield gr.update(value=log_suffix + f"Optimizing previews... {percent}% ({idx + 1}/{total_files})")
            
    msg = f"Optimized {optimized_count} existing previews, skipped {skipped_count} already optimized cards."
    yield gr.update(value=log_suffix + msg)

def toggle_search_replace_box (insertion_type):
    return (gr.update(visible= insertion_type == "SEARCH & REPLACE"))

def toggle_wildpath_box (toggle_status):
    return (
        gr.update(visible= toggle_status),
        gr.update(visible= not toggle_status)
    )

def selection_sequence(use_wild_path, selected_wildcard, selected_wild_path):
    if not ((selected_wild_path and selected_wild_path != "") or (not use_wild_path and selected_wildcard)):
        return []

    wild_paths = collect_gallery_cards(WILDCARDS_FOLDER)
    if use_wild_path:
        clean_prefix = (selected_wild_path or "").replace("*", "").replace(WILD_STR, "").strip().lower()
        if clean_prefix:
            return [item for item in wild_paths if item.lower().startswith(clean_prefix)]
        return []

    if selected_wildcard:
        selected_set = set(selected_wildcard)
        return [item for item in wild_paths if item in selected_set]

    return []

# Alias for backward compatibility
selection_sequance = selection_sequence

class Script(scripts.Script):
    is_txt2img = False

    def __init__(self):
        self.is_running = False

    def title(self):
        return "Wildcard Gallery Neo Preview Manager"

    def ui(self, is_img2img):
        with gr.Column(elem_classes=["wildcard_gallery_preview_manager_container"]):
            use_wild_path       = gr.Checkbox (label ="Use Wildcard Branch Selector", value = False, elem_classes=["wildcard_gallery_checkbox_container"])
            selected_wild_path  = gr.Dropdown (label ="Wildcard Parent Branch" , choices=collect_wildcard_branches(), interactive = True , info="Select the wildcard parent branch to process" , visible= False)
            selected_wildcard = gr.Dropdown(label ="Wildcards" , interactive = True , choices= collect_gallery_cards(WILDCARDS_FOLDER), multiselect=True)
            
            with gr.Row():
                insertion_type =  gr.Dropdown (
                                choices = ["AFTER", "BEFORE", "SEARCH & REPLACE"],
                                label="Wildcard Insertion Method",
                                value= "AFTER", 
                                interactive = True , 
                                info="Choose how and where to insert the wildcard within the prompt" )
                replace_str_opt = gr.Textbox(label="Search & Replace Text" , interactive = True , info="Search and replace the provided text by the wildcard in the prompt", visible= False )

            with gr.Accordion(open=False, label="Actions"):
                    with gr.Column():
                        task_override = gr.Checkbox(label ="Override Existing Previews"  ,value = False, elem_classes=["wildcard_gallery_checkbox"])
                        with gr.Row(elem_classes=["wildcard_gallery_actions_row"]):
                            act_count   = gr.Button(value = "📊 Count Selected", elem_classes=["wildcard_gallery_btn"])
                            act_collect = gr.Button(value = "📥 Collect Previews", elem_classes=["wildcard_gallery_btn"])
                            act_optimize = gr.Button(value = "⚡ Optimize Previews", elem_classes=["wildcard_gallery_btn"])
                            act_delete = gr.Button(value = "🗑️ Delete Previews", elem_classes=["wildcard_gallery_btn", "wildcard_gallery_ngbutton"])
                        act_msg     = gr.Markdown(value = log_suffix+" ",  elem_id="wildcard_gallery_notif_area", elem_classes=["wildcard_gallery_notif_area"] )

        use_wild_path.change(fn=toggle_wildpath_box , inputs=use_wild_path, outputs= [selected_wild_path, selected_wildcard])
        insertion_type.change(fn= toggle_search_replace_box, inputs=insertion_type, outputs= replace_str_opt )
        act_collect.click(btn_collect_previews, inputs= [use_wild_path, selected_wildcard, selected_wild_path], outputs=act_msg)
        act_count.click(btn_count_wildcards,   inputs= [use_wild_path, selected_wildcard, selected_wild_path], outputs=act_msg)
        act_delete.click(btn_delete_previews, inputs= [use_wild_path, selected_wildcard, selected_wild_path], outputs=act_msg)
        act_optimize.click(btn_optimize_previews, inputs= [], outputs=act_msg)
        
        
        return [selected_wild_path , task_override ,replace_str_opt, selected_wildcard, use_wild_path, insertion_type]
    
    
    
    def show(self, is_img2img):
        return not is_img2img

    def run(self, p,selected_wild_path , task_override,  replace_str_opt, selected_wildcard, use_wild_path, insertion_type):
        if self.is_running:
            return txt2img_process(p, [], replace_str_opt, task_override, insertion_type)
        
        self.is_running = True
        try:
            selected_wild_paths = selection_sequance (use_wild_path, selected_wildcard, selected_wild_path)
            if(selected_wild_paths):
                return txt2img_process(p,selected_wild_paths ,replace_str_opt , task_override, insertion_type)
            else:
                return txt2img_process(p,[] ,replace_str_opt , task_override, insertion_type)
        finally:
            self.is_running = False

# Backwards compatibility alias
CodexCards = WildcardGalleryCards

script_callbacks.on_before_ui(lambda: register_page(WildcardGalleryCards()))
