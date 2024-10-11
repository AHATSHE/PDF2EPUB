import pytest
import os
import json
import logging
from pdf2epub.pdf_parser import PDFParser
from utils.logging_config import setup_logging

setup_logging(log_file='logs/test.log', level=logging.DEBUG)

@pytest.fixture
def parser_instance():
    return PDFParser()

@pytest.fixture(params=['book_1.pdf', 'book_2.pdf', 'book_3.pdf'])
def pdf_file(request):
    return os.path.join('examples', 'pdf', request.param)

@pytest.fixture
def out_dir(parser_instance, pdf_file):
    # Process the PDF file
    parser_instance.process_pdf(pdf_file)
    # get file name
    base_name = os.path.basename(pdf_file)
    file_name = os.path.splitext(base_name)[0]
    return os.path.join(parser_instance.base_out_dir, file_name)

def test_files_created_and_valid_json(out_dir):
    text_dir = os.path.join(out_dir, 'content', 'text')
    image_dir = os.path.join(out_dir, 'content', 'images')
    # Check text output files
    for filename in ['text_spans.json', 'text_blocks.json', 'text_classes.json']:
        filepath = os.path.join(text_dir, filename)
        assert os.path.isfile(filepath), f"{filename} does not exist"

        # Check if the file contains valid JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                json.load(f)
            except json.JSONDecodeError:
                pytest.fail(f"{filename} contains invalid JSON")
    
    # Check image output files
    for filename in ['image_info.json']:
        filepath = os.path.join(image_dir, filename)
        assert os.path.isfile(filepath), f"{filename} does not exist"

        # Check if the file contains valid JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                json.load(f)
            except json.JSONDecodeError:
                pytest.fail(f"{filename} contains invalid JSON")

def test_blocks_have_unique_ids(out_dir):
    text_dir = os.path.join(out_dir, 'content', 'text')
    with open(os.path.join(text_dir, 'text_blocks.json'), 'r', encoding='utf-8') as f:
        text_blocks = json.load(f)

    block_ids = [block['id'] for block in text_blocks]
    assert len(block_ids) == len(set(block_ids)), "Text block IDs are not unique"

def test_blocks_contain_spans(out_dir):
    text_dir = os.path.join(out_dir, 'content', 'text')
    with open(os.path.join(text_dir, 'text_blocks.json'), 'r', encoding='utf-8') as f:
        text_blocks = json.load(f)

    for block in text_blocks:
        assert 'span_ids' in block, f"Block {block['id']} missing 'span_ids'"
        assert len(block['span_ids']) > 0, f"Block {block['id']} contains no spans"

def test_classes_have_unique_font_size_pairs(out_dir):
    text_dir = os.path.join(out_dir, 'content', 'text')
    with open(os.path.join(text_dir, 'text_classes.json'), 'r', encoding='utf-8') as f:
        text_classes = json.load(f)

    font_size_pairs = set()
    for class_info in text_classes.values():
        font_size_pair = (class_info['font'], class_info['size'])
        assert font_size_pair not in font_size_pairs, f"Duplicate font-size pair {font_size_pair}"
        font_size_pairs.add(font_size_pair)

def test_spans_contain_valid_characters(out_dir):
    text_dir = os.path.join(out_dir, 'content', 'text')
    with open(os.path.join(text_dir, 'text_spans.json'), 'r', encoding='utf-8') as f:
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

def test_images_stored_in_correct_directory(out_dir):
    images_dir = os.path.join(out_dir, 'content', 'images', 'images')
    assert os.path.isdir(images_dir), "Images directory does not exist"

    image_info_path = os.path.join(out_dir, 'content', 'images', 'image_info.json')
    assert os.path.isfile(image_info_path), "image_info.json does not exist"

    with open(image_info_path, 'r', encoding='utf-8') as f:
        image_info = json.load(f)
    for image in image_info:
        image_filename = f"{image['id']}.{image['ext']}"
        image_path = os.path.join(images_dir, image_filename)
        assert os.path.isfile(image_path), f"Image file {image_filename} does not exist in images directory"

def test_image_filenames_in_proper_order(out_dir):
    images_dir = os.path.join(out_dir, 'content', 'images', 'images')
    image_files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
    image_ids = []
    for image_file in image_files:
        if image_file.startswith('image_'):
            image_id = int(image_file.split('_')[1].split('.')[0])
            image_ids.append(image_id)
    image_ids.sort()
    # Check that image IDs start from 1 and increment by 1 without gaps
    expected_ids = list(range(1, len(image_ids) + 1))
    assert image_ids == expected_ids, f"Image IDs are not in proper order or missing IDs (expected {expected_ids}, got {image_ids})"

def test_image_and_text_block_ids_do_not_overlap(out_dir):
    text_dir = os.path.join(out_dir, 'content', 'text')
    images_dir = os.path.join(out_dir, 'content', 'images')

    with open(os.path.join(text_dir, 'text_blocks.json'), 'r', encoding='utf-8') as f:
        text_blocks = json.load(f)
    text_block_ids = {block['id'] for block in text_blocks}

    with open(os.path.join(images_dir, 'image_info.json'), 'r', encoding='utf-8') as f:
        image_info = json.load(f)
    image_block_ids = {image['block_id'] for image in image_info}

    overlap = text_block_ids & image_block_ids
    assert not overlap, f"Block IDs overlap between text and images: {overlap}"