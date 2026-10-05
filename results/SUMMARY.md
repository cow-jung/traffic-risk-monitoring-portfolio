# Four-model presentation analysis summary

- Test images: 371
- Classes: wood / box / pet
- Common condition: imgsz=640, base conf=0.25, match IoU=0.5
- Best overall F1: **alope_181** (F1=0.7429, P=0.7410, R=0.7449)
- Lowest wood FP: **alope_181** (FP=133, FN=204)
- Lowest wood FN: **alope_121** (FN=188, FP=156)

## Wood FP/FN at conf 0.25

|Model|TP|FP|FN|Precision|Recall|F1|
|---|---:|---:|---:|---:|---:|---:|
|yolo11n_88|255|149|206|0.6312|0.5531|0.5896|
|alope_121|273|156|188|0.6364|0.5922|0.6135|
|alope_151|269|151|192|0.6405|0.5835|0.6107|
|alope_181|257|133|204|0.6590|0.5575|0.6040|

## Recommended confidence by wood F1

|Model|Recommended conf|F1|FP|FN|
|---|---:|---:|---:|---:|
|alope_121|0.30|0.6217|111|203|
|alope_151|0.30|0.6237|115|200|
|alope_181|0.30|0.6238|95|209|
|yolo11n_88|0.40|0.6005|61|237|

## Wood recall by size

Size rule: small <1%, medium 1~5%, large >=5% of image area.

|Size|Best model|Recall|
|---|---|---:|
|small|alope_181|0.1833|
|medium|alope_151|0.4713|
|large|alope_121|0.7261|

## Interpretation warning

- Model selection should consider FP, FN, confidence, size recall, and video stability together.
- Video flicker uses sampled frames and is not a full-frame benchmark.
- The 720p video is for presentation; numeric test results come from all 371 labeled test images.