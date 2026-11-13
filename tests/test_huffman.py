"""Tests for Huffman coding."""

from backend.algorithms import huffman


def test_build_and_decode_roundtrip():
    text = "the quick brown fox jumps over the lazy dog"
    codes, root, _ = huffman.build_huffman(text)
    bits, _ = huffman.huffman_encode(text, codes)
    decoded, _ = huffman.huffman_decode(bits, root)
    assert decoded == text


def test_prefix_free():
    text = "abracadabra alakazam"
    codes, _, _ = huffman.build_huffman(text)
    assert huffman.is_prefix_free(codes)


def test_compression_helps():
    text = "aaaaaabbbbbccccdddeefff" * 20
    codes, root, _ = huffman.build_huffman(text)
    bits, _ = huffman.huffman_encode(text, codes)
    # 8-bit baseline vs compressed
    assert len(bits) < len(text) * 8


def test_single_character():
    codes, root, _ = huffman.build_huffman("aaaa")
    assert codes == {"a": "0"}
    bits, _ = huffman.huffman_encode("aaaa", codes)
    decoded, _ = huffman.huffman_decode(bits, root)
    assert decoded == "aaaa"


def test_empty_input():
    codes, root, _ = huffman.build_huffman("")
    assert codes == {}
    assert root is None


def test_frequency_dict_input():
    freqs = {"a": 5, "b": 3, "c": 2}
    codes, root, _ = huffman.build_huffman(freqs)
    text = "aaabbc"
    bits, _ = huffman.huffman_encode(text, codes)
    decoded, _ = huffman.huffman_decode(bits, root)
    assert decoded == text


def test_decode_single_symbol_regression():
    """Regression: single-leaf tree previously crashed on decode."""
    codes, root, _ = huffman.build_huffman("aaaaaaa")
    bits, _ = huffman.huffman_encode("aaaaaaa", codes)
    decoded, _ = huffman.huffman_decode(bits, root)
    assert decoded == "aaaaaaa"
