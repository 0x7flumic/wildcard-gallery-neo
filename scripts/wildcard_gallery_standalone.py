import modules.scripts as scripts
from modules import processing
from utils.wildcard_manager import wildcard_manager
class WildcardGalleryNeoScript(scripts.Script):
    def title(self):
        return "Wildcard Gallery Neo"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return []

    def process(self, p, *args):
        if not wildcard_manager.wildcards:
            wildcard_manager.refresh_wildcards()

        def process_batch(prompts, seeds):
            new_prompts = []
            count = len(prompts)
            current_seeds = seeds if seeds and len(seeds) >= count else [p.seed + i for i in range(count)]
            
            for i, prompt in enumerate(prompts):
                seed = current_seeds[i]
                new_prompts.append(wildcard_manager.replace_wildcards(prompt, seed=seed))
            return new_prompts

        seeds = getattr(p, 'all_seeds', None)

        if hasattr(p, 'all_prompts') and p.all_prompts:
            p.all_prompts = process_batch(p.all_prompts, seeds)
            if p.all_prompts:
                p.prompt = p.all_prompts[0]
        elif p.prompt:
            p.prompt = wildcard_manager.replace_wildcards(p.prompt, seed=p.seed)

        if hasattr(p, 'all_negative_prompts') and p.all_negative_prompts:
             p.all_negative_prompts = process_batch(p.all_negative_prompts, seeds)
             if p.all_negative_prompts:
                 p.negative_prompt = p.all_negative_prompts[0]
        elif p.negative_prompt:
             p.negative_prompt = wildcard_manager.replace_wildcards(p.negative_prompt, seed=p.seed)

        if hasattr(p, 'all_hr_prompts') and p.all_hr_prompts:
             p.all_hr_prompts = process_batch(p.all_hr_prompts, seeds)
             if p.all_hr_prompts:
                 p.hr_prompt = p.all_hr_prompts[0]
        elif hasattr(p, 'hr_prompt') and p.hr_prompt:
             p.hr_prompt = wildcard_manager.replace_wildcards(p.hr_prompt, seed=p.seed)

        if hasattr(p, 'all_hr_negative_prompts') and p.all_hr_negative_prompts:
             p.all_hr_negative_prompts = process_batch(p.all_hr_negative_prompts, seeds)
             if p.all_hr_negative_prompts:
                 p.hr_negative_prompt = p.all_hr_negative_prompts[0]
        elif hasattr(p, 'hr_negative_prompt') and p.hr_negative_prompt:
             p.hr_negative_prompt = wildcard_manager.replace_wildcards(p.hr_negative_prompt, seed=p.seed)
