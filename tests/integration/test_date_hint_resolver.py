"""Integration tests for date_hint resolver with holidays"""
import pytest
import asyncio
from agent.tools.calendar.date_resolver import get_resolver


class TestDateHintWithHolidays:
    """Test date hint resolver with various holiday queries in Hebrew and English"""

    @pytest.mark.asyncio
    async def test_chanukah_2027_hebrew(self):
        """חנוכה 2027"""
        resolver = get_resolver()
        result = await resolver.resolve("חנוכה 2027", default_nights=1)

        assert result.check_in.startswith("2027-"), f"Expected 2027, got {result.check_in}"
        assert result.nights >= 1, f"Expected at least 1 night, got {result.nights}"
        print(f"✓ חנוכה 2027: {result.check_in} to {result.check_out} ({result.nights} nights)")

    @pytest.mark.asyncio
    async def test_hanukkah_2027_english(self):
        """Hanukkah 2027 in English"""
        resolver = get_resolver()
        result = await resolver.resolve("Hanukkah 2027", default_nights=1)

        assert result.check_in.startswith("2027-"), f"Expected 2027, got {result.check_in}"
        assert result.nights >= 1, f"Expected at least 1 night, got {result.nights}"
        print(f"✓ Hanukkah 2027: {result.check_in} to {result.check_out} ({result.nights} nights)")

    @pytest.mark.asyncio
    async def test_pesach_2026_hebrew(self):
        """פסח 2026"""
        resolver = get_resolver()
        result = await resolver.resolve("פסח 2026", default_nights=1)

        assert result.check_in.startswith("2026-"), f"Expected 2026, got {result.check_in}"
        assert result.nights >= 1, f"Expected at least 1 night, got {result.nights}"
        print(f"✓ פסח 2026: {result.check_in} to {result.check_out} ({result.nights} nights)")

    @pytest.mark.asyncio
    async def test_passover_2026_english(self):
        """Passover 2026 in English"""
        resolver = get_resolver()
        result = await resolver.resolve("Passover 2026", default_nights=1)

        assert result.check_in.startswith("2026-"), f"Expected 2026, got {result.check_in}"
        assert result.nights >= 1, f"Expected at least 1 night, got {result.nights}"
        print(f"✓ Passover 2026: {result.check_in} to {result.check_out} ({result.nights} nights)")

    @pytest.mark.asyncio
    async def test_christmas_2026(self):
        """First night of Christmas 2026"""
        resolver = get_resolver()
        result = await resolver.resolve("first night of Christmas 2026", default_nights=1)

        assert result.check_in == "2026-12-24" or result.check_in == "2026-12-25"
        assert result.nights == 1
        print(f"✓ Christmas 2026: {result.check_in} to {result.check_out}")

    @pytest.mark.asyncio
    async def test_rosh_hashanah_next_occurrence(self):
        """Rosh Hashanah - next occurrence (should auto-advance to 2026)"""
        resolver = get_resolver()
        result = await resolver.resolve("Rosh Hashanah", default_nights=2)

        # Should return 2026 since 2025 already passed
        assert result.check_in.startswith("2026-")
        assert result.nights == 2
        print(f"✓ Rosh Hashanah (next): {result.check_in} to {result.check_out}")

    @pytest.mark.asyncio
    async def test_yom_kippur_hebrew(self):
        """יום כיפור"""
        resolver = get_resolver()
        result = await resolver.resolve("יום כיפור", default_nights=1)

        # Should return next occurrence
        assert result.nights == 1
        print(f"✓ יום כיפור: {result.check_in} to {result.check_out}")

    @pytest.mark.asyncio
    async def test_purim_2027(self):
        """Purim 2027"""
        resolver = get_resolver()
        result = await resolver.resolve("Purim 2027", default_nights=1)

        assert result.check_in.startswith("2027-")
        assert result.nights == 1
        print(f"✓ Purim 2027: {result.check_in} to {result.check_out}")

    @pytest.mark.asyncio
    async def test_sukkot_week(self):
        """Week during Sukkot"""
        resolver = get_resolver()
        result = await resolver.resolve("one week during Sukkot", default_nights=7)

        assert result.nights == 7
        print(f"✓ Sukkot week: {result.check_in} to {result.check_out} ({result.nights} nights)")

    @pytest.mark.asyncio
    async def test_shavuot_next(self):
        """Shavuot next year"""
        resolver = get_resolver()
        result = await resolver.resolve("Shavuot next year", default_nights=2)

        assert result.nights == 2
        print(f"✓ Shavuot next year: {result.check_in} to {result.check_out}")


if __name__ == "__main__":
    """Run tests manually"""
    print("=" * 70)
    print("DATE HINT RESOLVER - Holiday Tests")
    print("=" * 70)
    print()

    async def run_all_tests():
        test_instance = TestDateHintWithHolidays()

        tests = [
            ("חנוכה 2027 (Hebrew)", test_instance.test_chanukah_2027_hebrew),
            ("Hanukkah 2027 (English)", test_instance.test_hanukkah_2027_english),
            ("פסח 2026 (Hebrew)", test_instance.test_pesach_2026_hebrew),
            ("Passover 2026 (English)", test_instance.test_passover_2026_english),
            ("Christmas 2026", test_instance.test_christmas_2026),
            ("Rosh Hashanah (auto-next)", test_instance.test_rosh_hashanah_next_occurrence),
            ("יום כיפור (Hebrew)", test_instance.test_yom_kippur_hebrew),
            ("Purim 2027", test_instance.test_purim_2027),
            ("Sukkot week", test_instance.test_sukkot_week),
            ("Shavuot next year", test_instance.test_shavuot_next),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                print(f"\nTesting: {name}")
                await test_func()
                passed += 1
            except Exception as e:
                import traceback
                print(f"✗ FAILED: {e}")
                traceback.print_exc()
                failed += 1

        print()
        print("=" * 70)
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 70)

    asyncio.run(run_all_tests())
