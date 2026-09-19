import onnx
from onnx import TensorProto

for path in ["clip_vision_encoder_fp32.onnx", "clip_text_encoder_fp32.onnx"]:
    m = onnx.load(path)
    types = {}
    for init in m.graph.initializer:
        types[init.data_type] = types.get(init.data_type, 0) + 1
    print(f"\n{path}:")
    for t, cnt in types.items():
        print(f"  {TensorProto.DataType.Name(t)}: {cnt}")