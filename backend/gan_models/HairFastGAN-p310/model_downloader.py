from huggingface_hub import snapshot_download

# 저장소의 모든 파일을 'pretrained_models' 폴더로 다운로드
snapshot_download(
    repo_id="AIRI-Institute/HairFastGAN", 
    local_dir="./pretrained_models",
    local_dir_use_symlinks=False
)
print("다운로드 완료!")