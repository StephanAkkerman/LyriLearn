"""
Word/phrase alignment using SimAlign (mBERT) with version-agnostic method handling.
"""

from functools import lru_cache
from typing import Dict, Iterable, List, Set, Tuple

from simalign import SentenceAligner

PREFERENCE = ["itermax", "mwmf", "inter"]  # order if available


@lru_cache(maxsize=1)
def _aligner() -> SentenceAligner:
    # Don't pass matching_methods — avoids KeyError on unknown names
    return SentenceAligner(model="bert", token_type="bpe")


def _first_present(d: dict, keys: Iterable[str]) -> Set[Tuple[int, int]]:
    for k in keys:
        if k in d and d[k]:
            return d[k]
    # fall back to any available key
    for k, v in d.items():
        if v:
            return v
    return set()


def align_tokens(
    src_tokens: List[str], tgt_tokens: List[str]
) -> List[Dict[str, List[int]]]:
    """
    Return many-to-many alignment groups as:
      [{"l2": [i,...], "l1": [j,...]}, ...]
    where i indexes src_tokens (L2) and j indexes tgt_tokens (L1).
    """
    if not src_tokens or not tgt_tokens:
        return []

    al = _aligner().get_word_aligns(
        src_tokens, tgt_tokens
    )  # dict: method -> set[(i,j)]
    pairs = _first_present(al, PREFERENCE)

    # Build connected components over a bipartite graph of links
    from collections import defaultdict, deque

    g = defaultdict(set)

    for i, j in pairs:
        g[("l2", i)].add(("l1", j))  # <-- [] index, not () call
        g[("l1", j)].add(("l2", i))  # <-- [] index, not () call

    seen = set()
    groups: List[Dict[str, List[int]]] = []

    for node in list(g.keys()):
        if node in seen:
            continue
        comp_l2, comp_l1 = set(), set()
        q = deque([node])
        seen.add(node)
        while q:
            side, idx = q.popleft()
            (comp_l2 if side == "l2" else comp_l1).add(idx)
            for nb in g[(side, idx)]:
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        groups.append({"l2": sorted(comp_l2), "l1": sorted(comp_l1)})

    # Ensure every token appears at least in a singleton (optional)
    linked_l2 = {i for grp in groups for i in grp["l2"]}
    linked_l1 = {j for grp in groups for j in grp["l1"]}
    for i in range(len(src_tokens)):
        if i not in linked_l2:
            groups.append({"l2": [i], "l1": []})
    for j in range(len(tgt_tokens)):
        if j not in linked_l1:
            groups.append({"l2": [], "l1": [j]})

    return groups


if __name__ == "__main__":
    s = ["Kucari", "kau", "ke", "sana"]
    t = ["I", "looked", "for", "you", "there"]
    print(align_tokens(s, t))  # should print a list of groups without exceptions
