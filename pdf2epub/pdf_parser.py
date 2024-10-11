import pymupdf 
import os
import json
import random
import logging

class PDFParser:
    def __init__(self, base_out_dir='out', text_size_tolerance=0.2):
        self.base_out_dir = base_out_dir
        self.text_spans = []
        self.text_blocks = []
        self.classes = {}
        self.class_mapping = {}
        self.class_id_counter = 1
        self.span_id_counter = 1
        self.image_id_counter = 1
        self.image_info = []
        self.logger = logging.getLogger(__name__)
        self.current_file_name = ''
        self.current_document = None
        self.text_size_tolerance = text_size_tolerance
    
    def process_pdf(self, pdf_file):
        try:
            self.current_document = pymupdf.open(pdf_file)
            base_name = os.path.basename(pdf_file)
            self.current_file_name = os.path.splitext(base_name)[0]
        except Exception as e:
            self.logger.error(f"Failed to open PDF file {pdf_file}: {e}")
            return
        
        self.extract_content(self.current_document, self.text_size_tolerance)
        self.save_text_data()
        self.save_image_data()

        self.logger.info(f'Finished processing {self.current_file_name}')
        self.current_document.close()
    
    def extract_content(self, doc, size_tolerance):
        try:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                blocks = page.get_text("dict")["blocks"]
                # get image info for the page
                page_image_infos = page.get_image_info(hashes=False, xrefs=True)
                for block in blocks:
                    if block['type'] == 0:  # text block
                        self.process_text_block(block, page_num, size_tolerance)
                    elif block['type'] == 1: # image block
                        self.process_image_block(block, page_num, page_image_infos)
            self.logger.info(f"Finished extracting content from {self.current_file_name}")
        except Exception as e:
            self.logger.error(f"Error extracting content from {self.current_file_name}: {e}")
    
    def process_text_block(self, block, page_num, size_tolerance):
        try:
            block_spans = []

            # get block id
            block_id = f"block_{page_num}.{block['number']}"
            
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
                    'bbox': block['bbox'],
                    'span_ids': block_spans,
                }
                self.text_blocks.append(block_data)
                self.logger.debug(f"Processed text block {block_id} with {len(block_spans)} spans")
        except Exception as e:
            self.logger.error(f"Error extracting text block {block_id} from {self.current_file_name}: {e}")

    def process_image_block(self, block, page_num, page_image_infos):
        try:
            # get block id
            block_id = f"block_{page_num}.{block['number']}"

            # find matching image in image info
            image_info = next((info for info in page_image_infos if info['number'] == block['number']), None)

            if image_info is None:
                self.logger.warning(f"No matching image info found for block {block_id}")
                return

            xref = image_info.get('xref')
            if xref is None or xref == 0:
                self.logger.warning(f"No xref founf for image in block {block_id}")
                return

            # extract image
            try: 
                image_data = self.current_document.extract_image(xref)
            except Exception as e:
                self.logger.error(f"Failed to extract image xref from image block {block_id}: {e}")
                return

            image_bytes = image_data['image']
            image_ext = image_data['ext']
            image_width = image_data['width']
            image_height = image_data['height']
            
            # get image id
            image_id = f"image_{self.image_id_counter}"
            self.image_id_counter += 1

            # save image
            self.save_image(image_id, image_bytes, image_ext)

            image_data = {
                'id': image_id,
                'block_id': block_id,
                'bbox': block['bbox'],
                'width': image_width,
                'height': image_height,
                'ext': image_ext
            }
            self.image_info.append(image_data)
            self.logger.debug(f"Processed image block {block_id} containing image {image_id}")
        except Exception as e:
            self.logger.error(f"Error extracting image block {block_id} from {self.current_file_name}: {e}")
        
    # saves individual images
    def save_image(self, image_id, image_bytes, image_ext):
        images_dir = os.path.join(self.base_out_dir, self.current_file_name, 'content', 'images', 'images')
        os.makedirs(images_dir, exist_ok=True)
        image_filename = f"{image_id}.{image_ext}"
        image_path = os.path.join(images_dir, image_filename)

        try: 
            with open(image_path, 'wb') as img_file:
                img_file.write(image_bytes)
            self.logger.info(f"Saved image {image_id} to {image_path}")
        except Exception as e:
            self.logger.error(f"Failed to save image {image_id}: {e}")
            return
        
    # assigns class id based on font-size pair
    def get_class_id(self, font, size, size_tolerance):
        rounded_size = round(size / size_tolerance) * size_tolerance
        font_size_key = (font, rounded_size)

        if font_size_key not in self.class_mapping:
            class_id = f"class_{self.class_id_counter}"
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

    def save_text_data(self):
        out_dir = os.path.join(self.base_out_dir, self.current_file_name, 'content', 'text')

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

    def save_image_data(self):
        out_dir = os.path.join(self.base_out_dir, self.current_file_name, 'content', 'images')

        try:
            # ensure dir
            os.makedirs(out_dir, exist_ok=True)
            self.logger.info(f"Saving text data to directory: {out_dir}")

            # save image info
            image_info_path = os.path.join(out_dir, 'image_info.json')
            with open(image_info_path, 'w', encoding='utf-8') as f:
                json.dump(self.image_info, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved text spans to {image_info_path}")
        except Exception as e:
            self.logger.error(f"Failed to save image data: {e}")
