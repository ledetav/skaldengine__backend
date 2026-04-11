import uuid
import datetime
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.chat.models import Chat
from app.domains.character.models import Character

class StatsService:
    """
    Сервис для работы со статистикой персонажей.
    """
    
    @staticmethod
    async def increment_total_chats(db: AsyncSession, character_id: uuid.UUID):
        """
        Инкрементирует общий счетчик чатов персонажа.
        """
        await db.execute(
            update(Character)
            .where(Character.id == character_id)
            .values(total_chats_count=Character.total_chats_count + 1)
        )
        # Мы не коммитим здесь, так как это обычно часть бОльшей транзакции

    @staticmethod
    async def refresh_monthly_stats(db: AsyncSession):
        """
        Пересчитывает статистику за ПРОШЕДШИЙ календарный месяц для всех персонажей.
        Например, если сейчас Апрель, метод посчитает чаты за Март и запишет в monthly_chats_count.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Определяем границы прошлого месяца
        if now.month == 1:
            prev_month = 12
            prev_year = now.year - 1
        else:
            prev_month = now.month - 1
            prev_year = now.year
            
        start_date = datetime.datetime(prev_year, prev_month, 1, tzinfo=datetime.timezone.utc)
        
        # Конец месяца: первое число следующего за ним месяца
        if prev_month == 12:
            end_date = datetime.datetime(prev_year + 1, 1, 1, tzinfo=datetime.timezone.utc)
        else:
            end_date = datetime.datetime(prev_year, prev_month + 1, 1, tzinfo=datetime.timezone.utc)
            
        # 1. Сначала сбрасываем всем в 0 (на случай если у кого-то не было чатов в этом месяце)
        await db.execute(update(Character).values(monthly_chats_count=0))
        
        # 2. Считаем чаты для каждого персонажа за указанный период
        query = (
            select(Chat.character_id, func.count(Chat.id))
            .where(and_(Chat.created_at >= start_date, Chat.created_at < end_date))
            .group_by(Chat.character_id)
        )
        result = await db.execute(query)
        stats = result.all()
        
        # 3. Обновляем каждого персонажа
        for char_id, count in stats:
            await db.execute(
                update(Character)
                .where(Character.id == char_id)
                .values(monthly_chats_count=count)
            )
        
        await db.commit()

    @staticmethod
    async def refresh_all_stats(db: AsyncSession):
        """
        Полностью пересчитывает статистику для всех персонажей:
        - total_chats_count: на основе всех записей в таблице chats
        - monthly_chats_count: на основе записей за прошлый календарный месяц
        
        Полезно при выполнении миграции для заполнения исторических данных.
        """
        # 1. Сначала считаем общий счетчик (total)
        total_query = (
            select(Chat.character_id, func.count(Chat.id))
            .group_by(Chat.character_id)
        )
        total_result = await db.execute(total_query)
        total_stats = total_result.all()
        
        # Сбрасываем всем в 0 перед обновлением
        await db.execute(update(Character).values(total_chats_count=0))
        
        for char_id, count in total_stats:
            await db.execute(
                update(Character)
                .where(Character.id == char_id)
                .values(total_chats_count=count)
            )
            
        # 2. Вызываем обновление за прошлый месяц
        await StatsService.refresh_monthly_stats(db)
        
        await db.commit()
