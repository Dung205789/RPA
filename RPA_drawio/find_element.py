#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import by_text
import by_image
import logging


# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_image_input(input_str: str) -> bool:
    """Kiểm tra xem đầu vào có phải là file ảnh"""
    image_pattern = re.compile(r".*\.(png|jpg|jpeg|bmp)$", re.IGNORECASE)
    return bool(image_pattern.match(input_str))

def find_element(url: str, input_value: str, driver=None, step_created_elements=None,
                 created_connectors=None, original_elements=None, return_all=False):
    """
    Hàm tổng quát với hỗ trợ created_elements.
    """
    if step_created_elements is None:
        step_created_elements = {}
    if created_connectors is None:
        created_connectors = {}
    if original_elements is None:
        original_elements = {}


    lower_input = input_value.lower().strip()

    # Kiểm tra connector reference: connector_from_stepX_to_stepY
    connector_match = re.search(r"connector_from_step(\d+)_to_step(\d+)", lower_input)
    if connector_match:
        from_step = int(connector_match.group(1))
        to_step = int(connector_match.group(2))

        if (from_step, to_step) in created_connectors:
            result = created_connectors[(from_step, to_step)]
            logger.info(f"Tìm thấy CONNECTOR: connector_from_step{from_step}_to_step{to_step} = {result}")
            return [result] if return_all else result
        else:
            logger.error(f"Không tìm thấy connector từ step {from_step} đến step {to_step}")
            logger.warning(f"Connectors hiện có: {created_connectors}")
            return ["//not-found"] if return_all else "//not-found"

    # Kiểm tra reference đến "element created in step X"
    if not is_image_input(input_value) and "element created in step" in lower_input:
        match = re.search(r"step (\d+)", lower_input)
        if match:
            step_num = int(match.group(1))
            if step_num in step_created_elements:
                logger.info(f"Tìm thấy REFERENCE: Sử dụng CSS Selector từ step {step_num}: {step_created_elements[step_num]}")
                result = step_created_elements[step_num]
                return [result] if return_all else result
            else:
                logger.error(f"Không tìm thấy element từ step {step_num}")
                return ["//not-found"] if return_all else "//not-found"

    # Nếu đầu vào là ảnh
    if is_image_input(input_value):
        logger.info("[IMAGE] Đầu vào là ảnh, tìm trực tiếp bằng ảnh...")
        result = by_image.process_url_with_image(url, input_value, driver=driver)
        return [result] if return_all else result

    logger.info("[TEXT] Đầu vào là text.")
    result = by_text.process_url_with_text(url, input_value, driver=driver, return_all=return_all)
    return result

if __name__ == "__main__":
    logger.info(find_element("https://app.diagrams.net/", r"http://localhost:8123/uploads/stepImg/stepImg__13__20250922.png"))