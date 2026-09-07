import os
import random
import yaml
import re

class WildcardManager:
    SAMP_REGEX = re.compile(r"__(\+?\d+)\$\$(?:([^\n_]*?)\$\$)?([a-zA-Z0-9_\-\./ ]+?)__")
    WILDCARD_PATTERN = re.compile(r"__([a-zA-Z0-9_\-\./ ]+?)__")
    VARIANT_PATTERN = re.compile(r"\{([^{}]+?)\}")

    def __init__(self, check_default_paths=True):
        self.wildcards = {}
        self.short_keys = {}
        self.ambiguous_keys = set()
        self.wildcard_dirs = []
        self.ignored_collections = set()
        self._txt_cache = {}
        if check_default_paths:
            self.find_wildcard_dirs()
        self.hidden_wildcards = set()
        self.refresh_wildcards()

    def find_wildcard_dirs(self):
        self.wildcard_dirs = []
        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            ext_root = os.path.dirname(current_script_dir)
            local_wildcards = os.path.join(ext_root, "wildcards")
            if os.path.isdir(local_wildcards):
                self.wildcard_dirs.append(local_wildcards)
        except Exception as e:
            print(f"[Wildcard Gallery Neo Error] Error resolving wildcards dir: {e}")
        
    def refresh_wildcards(self):
        new_wildcards = {}
        new_hidden_wildcards = set()
        new_short_keys = {}
        new_ambiguous = set()
        
        for root_dir in self.wildcard_dirs:
            for root, dirs, files in os.walk(root_dir):
                rel_root = os.path.relpath(root, root_dir)
                
                if rel_root != ".":
                    top_folder = rel_root.split(os.path.sep)[0].lower()
                    if top_folder in self.ignored_collections:
                        continue
                
                for file in files:
                    if file.lower().endswith(".txt"):
                        rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                        top_folder_logical = rel_path.split(os.path.sep)[0].lower()
                        if top_folder_logical in self.ignored_collections:
                             continue
                             
                        key = os.path.splitext(rel_path)[0].replace(os.path.sep, "/")
                        new_wildcards[key] = os.path.join(root, file)
                    elif file.lower().endswith(".yaml") or file.lower().endswith(".yml"):
                        rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                        top_folder_logical = rel_path.split(os.path.sep)[0].lower()
                        if top_folder_logical in self.ignored_collections:
                             continue
                             
                        self.parse_yaml_wildcard(os.path.join(root, file), new_wildcards, new_hidden_wildcards)
        
        # Build smart short-key lookup
        for full_key in new_wildcards.keys():
            short = full_key.split("/")[-1]
            if short in new_short_keys:
                new_ambiguous.add(short)
            else:
                new_short_keys[short] = full_key

        self.wildcards = new_wildcards
        self.hidden_wildcards = new_hidden_wildcards
        self.short_keys = new_short_keys
        self.ambiguous_keys = new_ambiguous
        self._txt_cache = {}
        
    def parse_yaml_wildcard(self, filepath, target_wildcards=None, target_hidden=None):
        if target_wildcards is None:
            target_wildcards = self.wildcards
        if target_hidden is None:
            target_hidden = self.hidden_wildcards
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    self._flatten_yaml_dict(data, prefix="", target_wildcards=target_wildcards, target_hidden=target_hidden)
        except Exception as e:
            print(f"[Wildcard Gallery Neo Error] Error parsing YAML wildcard {filepath}: {e}")

    def _flatten_yaml_dict(self, data, prefix="", target_wildcards=None, target_hidden=None):
        if target_wildcards is None:
            target_wildcards = self.wildcards
        if target_hidden is None:
            target_hidden = self.hidden_wildcards
            
        all_values = []
        for key, value in data.items():
            current_key = f"{prefix}/{key}" if prefix else str(key)
            if isinstance(value, list):
                serialized_list = []
                for v in value:
                    if isinstance(v, (dict, list)):
                        continue
                    elif v is not None:
                        serialized_list.append(str(v).strip())
                target_wildcards[current_key] = serialized_list
                all_values.extend(serialized_list)
            elif isinstance(value, dict):
                child_values = self._flatten_yaml_dict(value, current_key, target_wildcards, target_hidden)
                all_values.extend(child_values)
        
        if prefix and all_values:
            target_wildcards[prefix] = all_values
            target_hidden.add(prefix)
            
        return all_values

    def resolve_key(self, key):
        if key in self.wildcards:
            return key
        if key in self.short_keys and key not in self.ambiguous_keys:
            return self.short_keys[key]
        return None

    def get_wildcard_values(self, wildcard_key):
        resolved = self.resolve_key(wildcard_key)
        if resolved and resolved in self.wildcards:
            val = self.wildcards[resolved]
            if isinstance(val, list):
                return val
            elif isinstance(val, str) and os.path.isfile(val):
                if val in self._txt_cache:
                    return self._txt_cache[val]
                try:
                    with open(val, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                        self._txt_cache[val] = lines
                        return lines
                except Exception as e:
                    print(f"[Wildcard Gallery Neo Error] Error reading wildcard file {val}: {e}")
                    return []
        return []

    def process_variants(self, text, seed=None, rng=None):
        if "{" not in text:
            return text

        if rng is None:
            if seed is not None:
                rng = random.Random(seed)
            else:
                rng = random
        
        while True:
            match = self.VARIANT_PATTERN.search(text)
            if not match:
                break
            
            content = match.group(1)
            if "|" not in content:
                break

            options = re.split(r"(?<!\\)\|", content)
            clean_options = []
            weights = []

            for opt in options:
                opt_str = opt.replace(r"\|", "|").strip()
                if "::" in opt_str:
                    parts = opt_str.split("::", 1)
                    try:
                        weight = float(parts[0].strip())
                        weights.append(max(0.0, weight))
                        clean_options.append(parts[1].strip())
                        continue
                    except ValueError:
                        pass
                weights.append(1.0)
                clean_options.append(opt_str)

            if not clean_options:
                choice = ""
            elif any(w != 1.0 for w in weights):
                choice = rng.choices(clean_options, weights=weights, k=1)[0]
            else:
                choice = rng.choice(clean_options)
            
            text = text[:match.start()] + choice + text[match.end():]
            
        return text

    def replace_wildcards(self, prompt, seed=None, max_depth=20, recursion_depth=0, rng=None):
        if not prompt or recursion_depth > max_depth:
            return prompt

        if "{" not in prompt and "__" not in prompt:
            return prompt

        if rng is None:
            if seed is not None:
                rng = random.Random(seed)
            else:
                rng = random

        if "{" in prompt:
            prompt = self.process_variants(prompt, rng=rng)

        if "__" not in prompt:
            return prompt
        
        def sampling_replacer(m):
            raw_count = m.group(1)
            allow_replacement = raw_count.startswith("+")
            count = int(raw_count.lstrip("+"))
            sep = m.group(2) if m.group(2) is not None else ", "
            key = m.group(3).strip()
            
            resolved_key = self.resolve_key(key)
            if resolved_key:
                values = self.get_wildcard_values(resolved_key)
                if values and count > 0:
                    if allow_replacement:
                        choices = rng.choices(values, k=count)
                    else:
                        k = min(count, len(values))
                        choices = rng.sample(values, k)
                    
                    processed_choices = [self.replace_wildcards(c, max_depth=max_depth, recursion_depth=recursion_depth+1, rng=rng) for c in choices]
                    return sep.join(processed_choices)
            
            return m.group(0)

        prompt = self.SAMP_REGEX.sub(sampling_replacer, prompt)
        
        def replace(match):
            key = match.group(1).strip()
            resolved_key = self.resolve_key(key)
            
            if resolved_key:
                values = self.get_wildcard_values(resolved_key)
                if values:
                    replacement = rng.choice(values)
                    return self.replace_wildcards(replacement, max_depth=max_depth, recursion_depth=recursion_depth + 1, rng=rng)
            
            return match.group(0)

        return self.WILDCARD_PATTERN.sub(replace, prompt)

wildcard_manager = WildcardManager()
# Backwards compatibility alias
codex_manager = wildcard_manager
