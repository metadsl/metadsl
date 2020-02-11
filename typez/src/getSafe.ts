export default function getSafe<K, V>(
  m: Map<K, V>,
  k: K,
  default_?: V | undefined
): V {
  const v = m.get(k);
  if (!v) {
    if (default_ === undefined) {
      throw new Error();
    }
    m.set(k, default_);
    return default_;
  }
  return v;
}
