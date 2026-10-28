"""Ranking: our own MERGE SORT and BINARY SEARCH (CO5)."""


def merge_sort(items, key):
    """Stable merge sort, DESCENDING by key(item). O(n log n) time, O(n) extra space."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)    # CO5: divide
    right = merge_sort(items[mid:], key)
    merged = []                            # CO5: conquer - merge two sorted halves
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) >= key(right[j]):  # >= keeps equal items in original order (stable)
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def above_threshold(sorted_items, threshold, key):
    """CO5: BINARY SEARCH on a list sorted descending. Finds the first index whose key is
    below the threshold and returns everything before it. O(log n) search."""
    lo, hi = 0, len(sorted_items)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(sorted_items[mid]) >= threshold:
            lo = mid + 1
        else:
            hi = mid
    return sorted_items[:lo]
