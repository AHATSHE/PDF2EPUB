import pytest
import os
import json
from pdf2epub.pdf_parser import PDFParser

@pytest.fixture
def parser_instance():
    return PDFParser()

@pytest.fixture(params=['book_1.pdf', 'book_2.pdf', 'book_3.pdf'])
def pdf_file(request):
    return os.path.join('examples', 'pdf', request.param)

@pytest.fixture
def out_dir(pdf_file, parser_instance):
    # get file name
    base_name = os.path.basename(pdf_file)
    file_name = os.path.splitext(base_name)[0]
    return os.path.join(parser_instance.base_out_dir, file_name, 'content', 'text')

def test_files_created_and_valid_json(parser_instance, pdf_file, out_dir):
    parser_instance.extract_text(pdf_file)
    parser_instance.save_text_data(pdf_file)

    # Check that output files are created
    for filename in ['text_spans.json', 'text_blocks.json', 'text_classes.json']:
        filepath = os.path.join(out_dir, filename)
        assert os.path.isfile(filepath), f"{filename} does not exist"

        # Check if the file contains valid JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                json.load(f)
            except json.JSONDecodeError:
                pytest.fail(f"{filename} contains invalid JSON")

def test_blocks_have_unique_ids(parser_instance, pdf_file, out_dir):
    parser_instance.extract_text(pdf_file)
    parser_instance.save_text_data(pdf_file)

    with open(os.path.join(out_dir, 'text_blocks.json'), 'r', encoding='utf-8') as f:
        text_blocks = json.load(f)

    block_ids = [block['id'] for block in text_blocks]
    assert len(block_ids) == len(set(block_ids)), "Block IDs are not unique"

def test_blocks_contain_spans(parser_instance, pdf_file, out_dir):
    parser_instance.extract_text(pdf_file)
    parser_instance.save_text_data(pdf_file)

    with open(os.path.join(out_dir, 'text_blocks.json'), 'r', encoding='utf-8') as f:
        text_blocks = json.load(f)

    for block in text_blocks:
        assert 'span_ids' in block, f"Block {block['id']} missing 'span_ids'"
        assert len(block['span_ids']) > 0, f"Block {block['id']} contains no spans"

def test_classes_have_unique_font_size_pairs(parser_instance, pdf_file, out_dir):
    parser_instance.extract_text(pdf_file)
    parser_instance.save_text_data(pdf_file)

    with open(os.path.join(out_dir, 'text_classes.json'), 'r', encoding='utf-8') as f:
        text_classes = json.load(f)

    font_size_pairs = set()
    for class_info in text_classes.values():
        font_size_pair = (class_info['font'], class_info['size'])
        assert font_size_pair not in font_size_pairs, f"Duplicate font-size pair {font_size_pair}"
        font_size_pairs.add(font_size_pair)

def test_spans_contain_valid_characters(parser_instance, pdf_file, out_dir):
    parser_instance.extract_text(pdf_file)
    parser_instance.save_text_data(pdf_file)

    with open(os.path.join(out_dir, 'text_spans.json'), 'r', encoding='utf-8') as f:
        text_spans = json.load(f)

    for span in text_spans:
        text = span['text']
        assert isinstance(text, str), f"Span {span['id']} text is not a string"
        assert text.strip() != '', f"Span {span['id']} text is empty or whitespace"
        try:
            encoded_text = text.encode('utf-8')
            decoded_text = encoded_text.decode('utf-8')
            assert decoded_text == text, f"Span {span['id']} contains invalid UTF-8 characters"
        except UnicodeEncodeError:
            pytest.fail(f"Span {span['id']} contains characters that cannot be encoded to UTF-8")
        except UnicodeDecodeError:
            pytest.fail(f"Span {span['id']} contains invalid UTF-8 encoding")

