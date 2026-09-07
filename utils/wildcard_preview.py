from modules.processing import process_images, Processed, fix_seed
from modules.shared import state
from modules import images
import os
from .wildcard_common import (
    CARDS_FOLDER,
    WILD_STR,
)

def resize_as_thumbnail (img, tragetSize=512):
    if img.width > img.height :
        width = tragetSize
        height = round((img.height/img.width)*tragetSize)
    else:
        height = tragetSize
        width = round((img.width/img.height)*tragetSize)
    
    return images.resize_image(0, img, width, height)


def txt2img_process(p,selected_wild_paths, replace_str_opt = "", task_override=False, insertion_type = "AFTER"): 
  
    images_list = []
    all_prompts = []
    infotexts = []
    prefered_format = ".jpeg"

    original_prompt = p.prompt
    fix_seed(p)
    filtered_job_list = []
    job_count = 0 
    if selected_wild_paths:
        for wpath in selected_wild_paths: 
            save_file_name = os.path.join(CARDS_FOLDER, wpath.replace("/", os.path.sep))
            if os.path.exists(save_file_name + ".jpeg") or os.path.exists(save_file_name + ".jpg") or os.path.exists(save_file_name + ".png") or os.path.exists(save_file_name + ".webp"):
                if task_override:
                    filtered_job_list.append(wpath)
            else:
                filtered_job_list.append(wpath)
        
        job_count = len(filtered_job_list)
        state.job_count = job_count

        suffix = ""
        try:
            for idx, wpath in enumerate(filtered_job_list):
                if state.interrupted:
                    break

                state.job_no = idx
                p.seed = p.seed + 1

                if insertion_type == "SEARCH & REPLACE":
                    if replace_str_opt != "" and original_prompt.count(replace_str_opt) > 0:
                        p.prompt = original_prompt.replace(replace_str_opt, f"{WILD_STR}{wpath}{WILD_STR}", 1)
                    else:
                        p.prompt = original_prompt
                elif insertion_type == "BEFORE":
                    p.prompt = f"{WILD_STR}{wpath}{WILD_STR} {original_prompt}"
                else:
                    p.prompt = f"{original_prompt} {WILD_STR}{wpath}{WILD_STR}"
                
                proc = process_images(p)
                infotexts.append(proc.info)

                if proc.all_prompts:
                    all_prompts.append(proc.all_prompts[0])
                else:
                    all_prompts.append(proc.prompt)
                
                if len(proc.images) > 1:
                    images_list.append(proc.images[0])
                else:
                    images_list += proc.images
                
                if state.interrupted:
                    break

                save_file_name = os.path.join(CARDS_FOLDER, wpath.replace("/", os.path.sep)) + suffix + prefered_format

                final_image = proc.images[0]
                thumbnail_image = resize_as_thumbnail(final_image, 512)
                
                os.makedirs(os.path.dirname(save_file_name), exist_ok=True)
                images.save_image_with_geninfo(image=thumbnail_image, geninfo=proc.info, filename=save_file_name)
                
                from modules import devices
                devices.torch_gc()
        finally:
            p.prompt = original_prompt

    return Processed(p, images_list, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)
