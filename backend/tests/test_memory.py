import pytest

from app.memory.entity_extractor import EntityExtractor


class TestEntityExtractor:
    def setup_method(self):
        self.extractor = EntityExtractor()

    @pytest.mark.asyncio
    async def test_extract_entities(self):
        text = "John works at Google and lives in San Francisco"
        result = await self.extractor.extract(text)
        assert "entities" in result
        assert "relationships" in result
        assert len(result["entities"]) > 0

    @pytest.mark.asyncio
    async def test_extract_relationships(self):
        text = "Alice manages the engineering team at Microsoft"
        result = await self.extractor.extract(text)
        assert len(result["relationships"]) > 0

    @pytest.mark.asyncio
    async def test_extract_memories(self):
        text = "Important: remember to call the dentist tomorrow. The meeting went well today."
        memories = await self.extractor.extract_memories(text)
        assert len(memories) > 0
        for mem in memories:
            assert "content" in mem
            assert "importance" in mem
            assert "type" in mem
            assert "tags" in mem

    def test_classify_entity_person(self):
        entity_type = self.extractor._classify_entity("John", "John is a developer")
        assert entity_type in ["person", "concept"]

    def test_classify_entity_organization(self):
        entity_type = self.extractor._classify_entity("Acme", "Acme Inc is a company")
        assert entity_type in ["organization", "concept"]

    def test_assess_importance_high(self):
        importance = self.extractor._assess_importance("This is very important! Remember this!")
        assert importance > 0.5

    def test_assess_importance_low(self):
        importance = self.extractor._assess_importance("The weather is nice today")
        assert importance <= 0.5

    def test_extract_tags(self):
        tags = self.extractor._extract_tags("I need to finish my project by Friday")
        assert "professional" in tags
        assert "personal" in tags
