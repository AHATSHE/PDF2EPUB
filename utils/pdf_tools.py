import pymupdf
import random

def annotate_pdf_elements(pdf_path, output_path, element_type='blocks'):
    """
    Annotate PDF elements with random colors.

    Parameters:
    - pdf_path: Path to the input PDF file.
    - output_path: Path to save the annotated PDF file.
    - element_type: Type of element to annotate ('blocks', 'lines', 'spans').

    The function highlights each specified element type in the PDF with a randomly generated RGB color.
    """

    # Open the PDF document
    doc = pymupdf.open(pdf_path)

    # Iterate over each page in the document
    for page in doc:
        text_dict = page.get_text('dict')

        if element_type == 'blocks':
            for _, block in enumerate(text_dict['blocks']):
                bbox = block['bbox']
                x0, y0 = bbox[0], bbox[1]
                color = (random.random(), random.random(), random.random())
                annot = page.add_rect_annot(bbox)
                annot.set_colors({"fill": color})
                annot.set_opacity(0.5)
                # Set the message including block number and x0, y0
                message = f"Block {block['number']} \n Position: x0={x0}, y0={y0} \n Type {block['type']}"
                annot.set_info(content=message)
                annot.update()
        elif element_type == 'lines':
            for block in text_dict['blocks']:
                for line in block['lines']:
                    bbox = line['bbox']
                    color = (random.random(), random.random(), random.random())
                    annot = page.add_rect_annot(bbox)
                    annot.set_colors({"fill": color})
                    annot.set_opacity(0.5)
                    annot.update()
        elif element_type == 'spans':
            for block in text_dict['blocks']:
                for line in block['lines']:
                    for span in line['spans']:
                        bbox = span['bbox']
                        color = (random.random(), random.random(), random.random())
                        annot = page.add_rect_annot(bbox)
                        annot.set_colors({"fill": color})
                        annot.set_opacity(0.5)
                        annot.update()
        else:
            print('Invalid element_type:', element_type)
            return

    # Save the annotated PDF to the specified output path
    doc.save(output_path)


annotate_pdf_elements('examples/pdf/book_2.pdf', 'out/annotated_blocks.pdf', element_type='blocks')
