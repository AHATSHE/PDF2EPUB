import pymupdf 
import os
import json
import random
import logging

class PDFParser:
    def __init__(self, base_out_dir='out'):
        self.base_out_dir = base_out_dir
        self.text_spans = []
        self.text_blocks = []
        self.classes = {}
        self.class_mapping = {}
        self.class_id_counter = 1
        self.span_id_counter = 1
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, pdf_file, size_tolerance=0.2):
        try:
            doc = pymupdf.open(pdf_file)
        except Exception as e:
            self.logger.error(f"Failed to open PDF file {pdf_file}: {e}")
            return
        
        try:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block['type'] == 0:  # text block
                        self.process_block(block, page_num, size_tolerance)
            self.logger.info("Finished processing PDF file")
        except Exception as e:
            self.logger.error(f"Error processing PDF file {pdf_file}: {e}")
        finally:
            doc.close()
        

    def process_block(self, block, page_num, size_tolerance):
        # get block id
        block_id = f"block_{page_num}.{block['number']}"
        block_spans = []
        block_bbox = block['bbox']

        for line in block['lines']:
            for span in line['spans']:
                text_content = span['text'].strip()
                if not text_content:
                    continue  # ignore whitespace

                class_id = self.get_class_id(span['font'], span['size'], size_tolerance)
                span_id = f"span_{self.span_id_counter}"
                self.span_id_counter += 1

                span_data = {
                    'id': span_id,
                    'text': text_content,
                    'class_id': class_id,
                    'block_id': block_id,
                    'bbox': span['bbox'],  # bounding box
                    'color': span['color'],
                }
                self.text_spans.append(span_data)
                block_spans.append(span_id)

        if block_spans:
            block_data = {
                'id': block_id,
                'bbox': block_bbox,
                'span_ids': block_spans,
            }
            self.text_blocks.append(block_data)
            self.logger.debug(f"Processed block {block_id} with {len(block_spans)} spans on page {page_num + 1}")
        
    # assigns class id based on font-size pair
    def get_class_id(self, font, size, size_tolerance):
        rounded_size = round(size / size_tolerance) * size_tolerance
        font_size_key = (font, rounded_size)

        if font_size_key not in self.class_mapping:
            class_id = f"class_f{self.class_id_counter}"
            self.class_mapping[font_size_key] = class_id
            self.classes[class_id] = {
                'font': font,
                'size': rounded_size
            }
            self.class_id_counter += 1
            self.logger.debug(f"Assigned new class ID {class_id} for font-size pair {font_size_key}")
        else:
            class_id = self.class_mapping[font_size_key]

        return class_id

    def save_text_data(self, pdf_file):
        # get file name
        base_name = os.path.basename(pdf_file)
        file_name = os.path.splitext(base_name)[0]

        out_dir = os.path.join(self.base_out_dir, file_name, 'content', 'text')

        # ensure dirs
        os.makedirs(out_dir, exist_ok=True)

        try:
            # ensure dir
            os.makedirs(out_dir, exist_ok=True)
            self.logger.info(f"Saving text data to directory: {out_dir}")

            # save text spans
            text_spans_path = os.path.join(out_dir, 'text_spans.json')
            with open(text_spans_path, 'w', encoding='utf-8') as f:
                json.dump(self.text_spans, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved text spans to {text_spans_path}")

            # save text blocks
            text_blocks_path = os.path.join(out_dir, 'text_blocks.json')
            with open(text_blocks_path, 'w', encoding='utf-8') as f:
                json.dump(self.text_blocks, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved text blocks to {text_blocks_path}")

            # save classes
            classes_path = os.path.join(out_dir, 'text_classes.json')
            # convert class IDs to strings for JSON 
            classes_serializable = {str(k): v for k, v in self.classes.items()}
            with open(classes_path, 'w', encoding='utf-8') as f:
                json.dump(classes_serializable, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved text classes to {classes_path}")
        except Exception as e:
            self.logger.error(f"Failed to save text data: {e}")

        

