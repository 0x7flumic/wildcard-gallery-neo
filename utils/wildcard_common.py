import os
import shutil
import errno
import stat

EXT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES_FOLDER = os.path.join(EXT_ROOT, "resources")
CARDS_FOLDER = os.path.join(EXT_ROOT, "cards")
WILDCARDS_FOLDER = []
WILD_STR = "__"
COLL_PREV_folder = os.path.join(EXT_ROOT, "COLLECTED_PREVIEWS")

from .wildcard_manager import wildcard_manager, codex_manager

def silentremove(filename):
    try:
        if os.path.exists(filename):
            os.chmod(filename, stat.S_IWRITE)
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT: 
            raise

_cached_gallery_cards = None

def invalidate_cards_cache():
    global _cached_gallery_cards
    _cached_gallery_cards = None

def collect_gallery_cards(wildcards_dirs=None, use_cache=True):
    global _cached_gallery_cards
    if use_cache and _cached_gallery_cards is not None:
        return _cached_gallery_cards

    all_wildcards = wildcard_manager.wildcards.keys()
    if hasattr(wildcard_manager, 'hidden_wildcards'):
        all_wildcards = [w for w in all_wildcards if w not in wildcard_manager.hidden_wildcards]
        
    _cached_gallery_cards = sorted(list(all_wildcards))
    return _cached_gallery_cards

# Backwards compatibility alias
collect_codex_cards = collect_gallery_cards

def get_safe_name_2(selected_wild_path, wild_paths_list=None):
    path_parts = selected_wild_path.split('/')
    parent = path_parts[-2] if len(path_parts) > 1 else ""
    return path_parts[-1], parent

def clean_residue(cards_dir=CARDS_FOLDER):
    """
    Purges any legacy 0-byte dummy .card files to maintain pure virtual cards.
    Removes empty subdirectories. Skips walk if directory does not exist.
    """
    if not os.path.exists(cards_dir):
        return

    has_legacy_cards = False
    for root, dirs, files in os.walk(cards_dir, topdown=False):
        for file in files:
            if file.lower().endswith(".card"):
                has_legacy_cards = True
                silentremove(os.path.join(root, file))

        for dirname in dirs:
            dir_to_check = os.path.join(root, dirname)
            try:
                if not os.listdir(dir_to_check):
                    os.rmdir(dir_to_check)
            except OSError:
                pass

def collect_previews(wildpath_selector, cards_dir=CARDS_FOLDER):
    collected_previews_list = []
    os.makedirs(COLL_PREV_folder, exist_ok=True)
    
    for wpath in wildpath_selector:
        base_path = os.path.join(os.path.abspath(cards_dir), wpath.replace("/", os.path.sep))
        for ext in [".jpeg", ".jpg", ".png", ".webp", ".gif"]:
            candidate = base_path + ext
            if os.path.isfile(candidate):
                collected_previews_list.append(candidate)
                try:
                    rel = os.path.relpath(candidate, cards_dir)
                    dest_file_path = os.path.join(COLL_PREV_folder, rel)
                    os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                    shutil.copy2(candidate, dest_file_path)
                except OSError:
                    print(f"[Wildcard Gallery Neo Error] Failed to collect [{candidate}]")
                break

    msg = f"{len(collected_previews_list)} previews were collected" if collected_previews_list else "no wildcard previews were collected"
    return msg

def delete_previews(wildpath_selector, cards_dir=CARDS_FOLDER):
    deleted_count = 0
    for wpath in wildpath_selector:
        base_path = os.path.join(os.path.abspath(cards_dir), wpath.replace("/", os.path.sep))
        for ext in [".jpeg", ".jpg", ".png", ".webp", ".gif"]:
            candidate = base_path + ext
            if os.path.isfile(candidate):
                try:
                    silentremove(candidate)
                    deleted_count += 1
                except OSError:
                    print(f"[Wildcard Gallery Neo Error] Failed to delete [{candidate}]")
                break

    msg = f"{deleted_count} previews were deleted" if deleted_count else "no wildcard previews were deleted"
    return msg

