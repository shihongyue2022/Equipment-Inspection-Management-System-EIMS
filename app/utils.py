from datetime import date


def get_deadline_status(next_inspection_date):
    """次回点検日から期限ステータスを算出する。

    戻り値:
        'overdue' : 超過
        'soon'    : まもなく（7日以内）
        'normal'  : 正常
        None      : 未点検（next_inspection_date が NULL）
    """
    if next_inspection_date is None:
        return None
    remaining_days = (next_inspection_date - date.today()).days
    if remaining_days < 0:
        return "overdue"
    if remaining_days <= 7:
        return "soon"
    return "normal"
