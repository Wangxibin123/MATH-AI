"""项目统一日志初始化。开发彩色可读，生产 JSON 直推日志平台。"""

from __future__ import annotations

import os
import sys
import logging
from loguru import logger


def setup_logging() -> None:
    """
    在任何代码 import loguru 之前执行一次（通常在 main.py 顶部）。
    读取环境变量：
        LOG_LEVEL : DEBUG / INFO / WARNING / ERROR / CRITICAL
        JSON_LOG  : 1 → JSON 行，0 → 彩色行
    """
    # 1⃣  清空 Loguru 默认 handler，避免重复输出
    logger.remove()

    # 2⃣  读取环境变量（默认 INFO + 彩色）
    level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    json_mode: bool = os.getenv("JSON_LOG", "0").lower() in {"1", "true"}

    if json_mode:
        # 3-a 生产：一行 JSON，可被 ELK / Loki 直接解析
        logger.add(
            sys.stdout,
            level=level,
            serialize=True,  # ★ 关键：输出 JSON
            backtrace=False,  # 线上别泄漏变量
            diagnose=False,
            enqueue=True,  # 多线程安全
        )
    else:
        # 3-b 开发：彩色 + 精简格式
        color_fmt = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            level=level,
            format=color_fmt,
            enqueue=False,  # 开发模式下通常不需要排队，除非有明确的多线程问题
        )

    # 4⃣  可选：把标准 logging / print 重定向到 Loguru
    # 注意：这个 InterceptHandler 比较基础，对于复杂的 logging 配置可能需要更完善的实现
    # 或者直接在项目中使用 logger.catch() 来捕获标准 logging 的异常
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # 获取对应的 Loguru 级别
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno  # type: ignore[assignment]

            # 查找调用栈帧以获取正确的模块、函数和行号
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back  # type: ignore
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True) # force=True 仅 Python 3.8+
    # 更兼容的方式是获取 root logger 并添加 handler
    logging.getLogger().handlers = [InterceptHandler()]
    logging.getLogger().setLevel(0)  # Process all messages from standard logging

    # 重定向 stdout 和 stderr 可能对某些工具或库产生副作用，谨慎使用
    # 如果确实需要，确保 InterceptHandler for print 足够鲁棒
    class PrintIntercept:
        def write(self, message: str) -> None:
            if message.strip():
                logger.opt(depth=1).info(
                    message.strip()
                )  # depth=1 因为是从 PrintIntercept.write 调用

        def flush(self) -> None:  # Needed for compatibility with some print scenarios
            pass

    # sys.stdout = PrintIntercept() # 谨慎开启
    # sys.stderr = PrintIntercept() # 谨慎开启

    logger.info(
        f"Loguru logging setup complete. Level: {level}, JSON mode: {json_mode}"
    )
