from enterprise_master_agent.data_api import _sales_summary_sql


def test_sales_summary_sql_is_fixed_readonly():
    sql, params = _sales_summary_sql("mtd")
    low = " ".join(sql.lower().split())
    assert low.startswith("with ")
    assert "sle.tblsalehdr" in low
    assert "sle.tblretsalehdr" in low
    assert params == ("mtd",)
    for token in (" insert ", " update ", " delete ", " merge ", " drop ", " alter ", " create ", " truncate ", " exec "):
        assert token not in f" {low} "


def test_sales_summary_sql_has_bounded_period():
    sql, _ = _sales_summary_sql("latest_day")
    low = " ".join(sql.lower().split())
    assert "between b.fromdate and b.todate" in low
    assert "max(saledate)" in low
