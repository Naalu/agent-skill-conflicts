"""Embed the distinct skill descriptions of the library sample.

Model  : sentence-transformers/all-MiniLM-L6-v2 (ONNX export Qdrant/all-MiniLM-L6-v2-onnx), fixed in RUNLOG before the run.
Pooling: attention-masked mean of the last hidden state, then L2 normalisation (the model's own recipe).
Input  : table sdesc (desc_id, text); texts are already lower-cased, whitespace-normalised and cut at 1,024 characters.
         Token sequences are truncated at 256 tokens, the model's maximum.
Output : out/emb.npy   float32 [n_descriptions, 384], row i = desc_id i.
Batches are formed from texts sorted by token count so that padding is minimal; this changes speed, not results.
"""
import glob, os, time
import duckdb, numpy as np, onnxruntime as ort
from tokenizers import Tokenizer

from huggingface_hub import hf_hub_download   # downloads once, then reads from the local Hugging Face cache
MODEL = hf_hub_download('Qdrant/all-MiniLM-L6-v2-onnx', 'model.onnx')
hf_hub_download('Qdrant/all-MiniLM-L6-v2-onnx', 'tokenizer.json')
MAX_TOKENS, TOKEN_BUDGET = 256, 6000

tok = Tokenizer.from_file(os.path.join(os.path.dirname(MODEL), 'tokenizer.json'))
tok.no_padding(); tok.enable_truncation(max_length=MAX_TOKENS)
so = ort.SessionOptions(); so.intra_op_num_threads = 2
sess = ort.InferenceSession(MODEL, so, providers=['CPUExecutionProvider'])

rows = duckdb.connect('collide.duckdb', read_only=True).execute("SELECT desc_id, text FROM sdesc ORDER BY desc_id").fetchall()
n = len(rows); assert [r[0] for r in rows] == list(range(n))
enc = tok.encode_batch([r[1] for r in rows])
ids = [e.ids for e in enc]
order = np.argsort([len(x) for x in ids], kind='stable')
out = np.lib.format.open_memmap('out/emb.npy', mode='w+', dtype=np.float32, shape=(n, 384))
t0, i = time.time(), 0
while i < n:
    L = len(ids[order[min(i + 7, n - 1)]])                      # look a little ahead to size the batch
    bs = max(8, min(256, TOKEN_BUDGET // max(L, 1)))
    idx = order[i:i + bs]; Lmax = max(len(ids[j]) for j in idx)
    a = np.zeros((len(idx), Lmax), dtype=np.int64); m = np.zeros_like(a)
    for r, j in enumerate(idx):
        a[r, :len(ids[j])] = ids[j]; m[r, :len(ids[j])] = 1
    h = sess.run(None, {'input_ids': a, 'attention_mask': m, 'token_type_ids': np.zeros_like(a)})[0]
    v = (h * m[:, :, None]).sum(1) / m.sum(1, keepdims=True)
    out[idx] = v / np.linalg.norm(v, axis=1, keepdims=True)
    i += len(idx)
    if (i // 5000) != ((i - len(idx)) // 5000):
        print(i, n, round(time.time() - t0), 's', flush=True)
out.flush(); print('done', n, round(time.time() - t0), 's', flush=True)
