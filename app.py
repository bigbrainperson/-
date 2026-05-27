"""
app.py — интерактивный дашборд Surf Coffee на Dash
Проект: Анализ открытия кофейни Surf Coffee рядом с ВШЭ

Закрывает тему курса: дашборды на Dash.

УСТАНОВКА:
    pip install dash plotly pandas

ЗАПУСК:
    python dashboard/app.py
    → открыть в браузере http://127.0.0.1:8050

Дашборд имеет 4 вкладки:
1. Конкуренты — рейтинги, форматы, география
2. Цены — меню Правда кофе, цена за 100 мл
3. Опрос — анализ аудитории ВШЭ
4. Финансы — сценарии, BEP, прогноз
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# ─────────────────────────────────────────────
# Загрузка данных
# ─────────────────────────────────────────────

DATA_DIR = "data"

def safe_read(path):
    """Безопасно читает CSV; если файла нет — возвращает пустой DataFrame."""
    full_path = os.path.join(DATA_DIR, path)
    if os.path.exists(full_path):
        return pd.read_csv(full_path)
    print(f"[ВНИМАНИЕ] Файл не найден: {full_path}")
    return pd.DataFrame()

df_competitors = safe_read("processed/competitors_processed.csv")
df_menu = safe_read("processed/pravda_menu_processed.csv")
df_yandex = safe_read("raw/yandex_maps_competitors.csv")
df_survey = safe_read("processed/survey_responses_processed.csv")
df_financial = safe_read("processed/financial_model.csv")
df_forecast = safe_read("processed/financial_forecast_year1.csv")


# ─────────────────────────────────────────────
# Инициализация Dash
# ─────────────────────────────────────────────

app = dash.Dash(__name__)
app.title = "Surf Coffee — анализ открытия"

# Базовый стиль
HEADER_STYLE = {
    "textAlign": "center",
    "color": "#2C3E50",
    "padding": "20px",
    "backgroundColor": "#F8F9FA",
    "borderBottom": "3px solid #4A90D9",
    "marginBottom": "20px",
}

CARD_STYLE = {
    "backgroundColor": "white",
    "borderRadius": "8px",
    "padding": "20px",
    "margin": "10px",
    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
}

# ─────────────────────────────────────────────
# Лэйаут приложения
# ─────────────────────────────────────────────

app.layout = html.Div([
    # Заголовок
    html.Div([
        html.H1("Surf Coffee на Покровском бульваре",
                style={"margin": "0", "fontSize": "32px"}),
        html.P("Интерактивный дашборд анализа открытия кофейни рядом с ВШЭ",
               style={"margin": "10px 0 0 0", "color": "#7F8C8D", "fontSize": "16px"}),
    ], style=HEADER_STYLE),

    # KPI карточки
    html.Div([
        html.Div([
            html.H3(f"{len(df_competitors)}", style={"color": "#4A90D9", "margin": "0", "fontSize": "36px"}),
            html.P("Конкурентов рядом", style={"margin": "5px 0 0 0", "color": "#7F8C8D"}),
        ], style={**CARD_STYLE, "textAlign": "center", "flex": "1"}),

        html.Div([
            html.H3(f"{len(df_survey)}", style={"color": "#E8A838", "margin": "0", "fontSize": "36px"}),
            html.P("Ответов опроса", style={"margin": "5px 0 0 0", "color": "#7F8C8D"}),
        ], style={**CARD_STYLE, "textAlign": "center", "flex": "1"}),

        html.Div([
            html.H3(f"{int(df_survey[df_survey.get('avg_price_rub', pd.Series([0])) > 0]['avg_price_rub'].mean()) if not df_survey.empty else 0} ₽",
                    style={"color": "#5BA85A", "margin": "0", "fontSize": "36px"}),
            html.P("Средний чек по опросу", style={"margin": "5px 0 0 0", "color": "#7F8C8D"}),
        ], style={**CARD_STYLE, "textAlign": "center", "flex": "1"}),

        html.Div([
            html.H3("173", style={"color": "#D95B5B", "margin": "0", "fontSize": "36px"}),
            html.P("Точка безубыточности (чеков/день)", style={"margin": "5px 0 0 0", "color": "#7F8C8D"}),
        ], style={**CARD_STYLE, "textAlign": "center", "flex": "1"}),
    ], style={"display": "flex", "padding": "0 20px"}),

    # Вкладки
    html.Div([
        dcc.Tabs(id="tabs", value="tab-competitors", children=[
            dcc.Tab(label="Конкуренты", value="tab-competitors"),
            dcc.Tab(label="Цены", value="tab-prices"),
            dcc.Tab(label="Опрос аудитории", value="tab-survey"),
            dcc.Tab(label="Финансы", value="tab-finance"),
        ]),
        html.Div(id="tabs-content", style={"padding": "20px"}),
    ], style={"margin": "20px"}),

    # Футер
    html.Div([
        html.P("Курс «Наука о данных», ВШЭ, spring 2026",
               style={"textAlign": "center", "color": "#95A5A6", "fontSize": "12px"}),
    ], style={"padding": "20px"}),
], style={"backgroundColor": "#ECF0F1", "minHeight": "100vh",
          "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"})


# ─────────────────────────────────────────────
# Колбэк: переключение вкладок
# ─────────────────────────────────────────────

@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value"),
)
def render_tab(tab):
    if tab == "tab-competitors":
        return render_competitors_tab()
    if tab == "tab-prices":
        return render_prices_tab()
    if tab == "tab-survey":
        return render_survey_tab()
    if tab == "tab-finance":
        return render_finance_tab()
    return html.Div("Выберите вкладку")


# ─────────────────────────────────────────────
# Вкладка 1: Конкуренты
# ─────────────────────────────────────────────

def render_competitors_tab():
    if df_competitors.empty:
        return html.Div("Нет данных о конкурентах")

    # График 1: распределение по форматам
    fmt_counts = df_competitors["format"].value_counts().reset_index()
    fmt_counts.columns = ["format", "count"]
    fig_formats = px.bar(
        fmt_counts, x="count", y="format", orientation="h",
        title="Конкуренты по форматам", color="count",
        color_continuous_scale="Blues",
        labels={"count": "Количество", "format": "Формат"},
    )
    fig_formats.update_layout(showlegend=False, height=350,
                              plot_bgcolor="white", coloraxis_showscale=False)

    # График 2: сеть vs не сеть
    chain_counts = df_competitors["is_chain"].value_counts().reset_index()
    chain_counts.columns = ["is_chain", "count"]
    chain_counts["label"] = chain_counts["is_chain"].map({True: "Сетевые", False: "Несетевые"})
    fig_chain = px.pie(
        chain_counts, values="count", names="label",
        title="Структура: сеть vs локальные",
        color_discrete_sequence=["#4A90D9", "#E8A838"],
    )
    fig_chain.update_layout(height=350)

    # График 3: рейтинги (если есть Яндекс данные)
    rating_chart = []
    if not df_yandex.empty and "rating" in df_yandex.columns:
        df_sorted = df_yandex.sort_values("rating", ascending=True)
        fig_ratings = px.bar(
            df_sorted, x="rating", y="name", orientation="h",
            title="Рейтинги конкурентов на Яндекс.Картах",
            color="rating", color_continuous_scale="Viridis",
            text="rating",
            labels={"rating": "Рейтинг", "name": "Заведение"},
        )
        fig_ratings.update_traces(textposition="outside")
        fig_ratings.update_layout(height=400, plot_bgcolor="white",
                                  xaxis_range=[4.3, 5.0], coloraxis_showscale=False)
        rating_chart = [dcc.Graph(figure=fig_ratings)]

    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_formats)], style={"flex": "1", **CARD_STYLE}),
            html.Div([dcc.Graph(figure=fig_chain)], style={"flex": "1", **CARD_STYLE}),
        ], style={"display": "flex"}),

        html.Div(rating_chart, style=CARD_STYLE) if rating_chart else html.Div(),

        html.Div([
            html.H3("Список конкурентов", style={"color": "#2C3E50"}),
            dash_table.DataTable(
                data=df_competitors[["name", "address", "format", "is_chain"]].to_dict("records"),
                columns=[
                    {"name": "Название", "id": "name"},
                    {"name": "Адрес", "id": "address"},
                    {"name": "Формат", "id": "format"},
                    {"name": "Сеть?", "id": "is_chain"},
                ],
                style_cell={"textAlign": "left", "padding": "10px",
                            "fontFamily": "inherit"},
                style_header={"backgroundColor": "#4A90D9", "color": "white",
                              "fontWeight": "bold"},
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#F8F9FA"},
                ],
            ),
        ], style=CARD_STYLE),
    ])


# ─────────────────────────────────────────────
# Вкладка 2: Цены
# ─────────────────────────────────────────────

def render_prices_tab():
    if df_menu.empty:
        return html.Div("Нет данных о ценах")

    key_drinks = df_menu[df_menu.get("is_key_drink", True) == True].sort_values("price_rub")

    fig_prices = px.bar(
        key_drinks, x="price_rub", y="drink_name", orientation="h",
        title="Цены на ключевые напитки «Правда кофе»",
        color="price_rub", color_continuous_scale="Oranges",
        text="price_rub",
        labels={"price_rub": "Цена, ₽", "drink_name": "Напиток"},
    )
    fig_prices.update_traces(texttemplate="%{text} ₽", textposition="outside")
    fig_prices.update_layout(height=450, plot_bgcolor="white",
                             coloraxis_showscale=False)

    fig_per100 = px.bar(
        key_drinks.sort_values("price_per_100ml"),
        x="price_per_100ml", y="drink_name", orientation="h",
        title="Цена за 100 мл (эффективность ценообразования)",
        color="price_per_100ml", color_continuous_scale="Reds",
        text="price_per_100ml",
        labels={"price_per_100ml": "Цена за 100 мл, ₽", "drink_name": "Напиток"},
    )
    fig_per100.update_traces(texttemplate="%{text:.1f} ₽", textposition="outside")
    fig_per100.update_layout(height=450, plot_bgcolor="white",
                             coloraxis_showscale=False)

    fig_scatter = px.scatter(
        df_menu.dropna(subset=["volume_ml", "price_rub"]),
        x="volume_ml", y="price_rub", text="drink_name",
        size="price_per_100ml", color="category",
        title="Объём vs цена напитков",
        labels={"volume_ml": "Объём, мл", "price_rub": "Цена, ₽",
                "category": "Категория"},
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(height=500, plot_bgcolor="white")

    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_prices)], style={"flex": "1", **CARD_STYLE}),
            html.Div([dcc.Graph(figure=fig_per100)], style={"flex": "1", **CARD_STYLE}),
        ], style={"display": "flex"}),
        html.Div([dcc.Graph(figure=fig_scatter)], style=CARD_STYLE),
    ])


# ─────────────────────────────────────────────
# Вкладка 3: Опрос
# ─────────────────────────────────────────────

def render_survey_tab():
    if df_survey.empty:
        return html.Div("Нет данных опроса")

    # Частота покупки
    freq_order = ["никогда", "1-2 раза в неделю", "3-4 раза в неделю", "каждый день"]
    freq_counts = df_survey["frequency_per_week"].value_counts().reindex(freq_order).reset_index()
    freq_counts.columns = ["frequency", "count"]

    fig_freq = px.bar(
        freq_counts, x="frequency", y="count",
        title="Как часто респонденты покупают кофе",
        color="count", color_continuous_scale="Blues",
        text="count",
        labels={"frequency": "Частота", "count": "Количество ответов"},
    )
    fig_freq.update_traces(textposition="outside")
    fig_freq.update_layout(height=400, plot_bgcolor="white", coloraxis_showscale=False)

    # Распределение чека
    buyers = df_survey[df_survey["avg_price_rub"] > 0]
    fig_price = px.histogram(
        buyers, x="avg_price_rub", nbins=15,
        title=f"Распределение среднего чека (n={len(buyers)})",
        labels={"avg_price_rub": "Цена за напиток, ₽", "count": "Количество"},
        color_discrete_sequence=["#4A90D9"],
    )
    fig_price.add_vline(x=buyers["avg_price_rub"].mean(),
                        line_dash="dash", line_color="red",
                        annotation_text=f"Среднее: {buyers['avg_price_rub'].mean():.0f} ₽")
    fig_price.update_layout(height=400, plot_bgcolor="white", showlegend=False)

    # Факторы
    all_factors = []
    for v in df_survey["important_factors"].fillna(""):
        all_factors.extend([f.strip() for f in v.split(";") if f.strip()])
    factor_counts = pd.Series(all_factors).value_counts().reset_index()
    factor_counts.columns = ["factor", "count"]

    fig_factors = px.bar(
        factor_counts.sort_values("count"), x="count", y="factor", orientation="h",
        title="Что важно для аудитории при выборе кофейни",
        color="count", color_continuous_scale="Viridis",
        text="count",
        labels={"count": "Упоминаний", "factor": "Фактор"},
    )
    fig_factors.update_traces(textposition="outside")
    fig_factors.update_layout(height=500, plot_bgcolor="white", coloraxis_showscale=False)

    return html.Div([
        html.Div([
            html.Div([dcc.Graph(figure=fig_freq)], style={"flex": "1", **CARD_STYLE}),
            html.Div([dcc.Graph(figure=fig_price)], style={"flex": "1", **CARD_STYLE}),
        ], style={"display": "flex"}),
        html.Div([dcc.Graph(figure=fig_factors)], style=CARD_STYLE),
    ])


# ─────────────────────────────────────────────
# Вкладка 4: Финансы
# ─────────────────────────────────────────────

def render_finance_tab():
    if df_financial.empty:
        return html.Div("Нет данных финансовой модели")

    # Слайдер для интерактивного выбора трафика
    return html.Div([
        html.Div([
            html.H3("Интерактивный калькулятор прибыли", style={"color": "#2C3E50"}),
            html.P("Сдвиньте слайдер, чтобы увидеть, как трафик влияет на прибыль:",
                   style={"color": "#7F8C8D"}),
            html.Div([
                html.Label("Чеков в день:", style={"fontWeight": "bold"}),
                dcc.Slider(
                    id="traffic-slider",
                    min=50, max=400, step=10, value=240,
                    marks={i: str(i) for i in range(50, 401, 50)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div(id="traffic-output", style={"marginTop": "20px"}),
        ], style=CARD_STYLE),

        # Прогноз на год
        html.Div([
            dcc.Graph(figure=build_forecast_chart())
        ], style=CARD_STYLE) if not df_forecast.empty else html.Div(),

        # Таблица сценариев
        html.Div([
            html.H3("Сценарии финмодели", style={"color": "#2C3E50"}),
            dash_table.DataTable(
                data=df_financial.reset_index().to_dict("records"),
                columns=[{"name": col, "id": col} for col in df_financial.reset_index().columns],
                style_cell={"textAlign": "right", "padding": "8px",
                            "fontFamily": "inherit", "fontSize": "13px"},
                style_header={"backgroundColor": "#4A90D9", "color": "white",
                              "fontWeight": "bold"},
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#F8F9FA"},
                ],
            ),
        ], style=CARD_STYLE),
    ])


def build_forecast_chart():
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_forecast["Месяц"],
        y=df_forecast["Накопленный денежный поток"],
        name="Накопленный кэш",
        marker_color=["#D95B5B" if v < 0 else "#5BA85A"
                      for v in df_forecast["Накопленный денежный поток"]],
        text=[f"{v/1_000_000:.1f}M" for v in df_forecast["Накопленный денежный поток"]],
        textposition="auto",
    ))
    fig.add_trace(go.Scatter(
        x=df_forecast["Месяц"],
        y=df_forecast["Операц. прибыль"],
        name="Операц. прибыль (мес)",
        mode="lines+markers",
        line=dict(color="#4A90D9", width=3),
        yaxis="y2",
    ))
    fig.update_layout(
        title="Прогноз на 12 месяцев",
        xaxis=dict(title="Месяц"),
        yaxis=dict(title="Накопленный кэш, ₽", side="left"),
        yaxis2=dict(title="Операц. прибыль, ₽", side="right", overlaying="y"),
        plot_bgcolor="white",
        height=450,
        legend=dict(x=0.02, y=0.98),
    )
    return fig


# ─────────────────────────────────────────────
# Колбэк: интерактивный калькулятор
# ─────────────────────────────────────────────

@app.callback(
    Output("traffic-output", "children"),
    Input("traffic-slider", "value"),
)
def update_traffic_calculation(checks_per_day):
    # Те же параметры, что в финмодели
    AVG_CHECK = 270
    COFFEE_REVENUE_SHARE = 0.65
    COFFEE_COGS_PCT = 0.28
    FOOD_COGS_PCT = 0.38
    FRANCHISE_FEE_PCT = 0.05
    FIXED_COSTS = 890_000  # аренда + ФОТ + маркетинг + коммуналка
    DAYS = 30

    revenue = checks_per_day * AVG_CHECK * DAYS
    coffee_rev = revenue * COFFEE_REVENUE_SHARE
    food_rev = revenue * (1 - COFFEE_REVENUE_SHARE)
    cogs = coffee_rev * COFFEE_COGS_PCT + food_rev * FOOD_COGS_PCT
    franchise = revenue * FRANCHISE_FEE_PCT
    profit = revenue - cogs - franchise - FIXED_COSTS
    margin = profit / revenue * 100 if revenue else 0

    profit_color = "#5BA85A" if profit > 0 else "#D95B5B"
    profit_label = "Прибыль" if profit > 0 else "Убыток"

    return html.Div([
        html.Div([
            html.H4("Выручка/месяц", style={"color": "#7F8C8D", "margin": "0"}),
            html.H3(f"{revenue:,.0f} ₽".replace(",", " "),
                    style={"color": "#4A90D9", "margin": "5px 0"}),
        ], style={"flex": "1", "textAlign": "center"}),

        html.Div([
            html.H4("Расходы/месяц", style={"color": "#7F8C8D", "margin": "0"}),
            html.H3(f"{cogs + franchise + FIXED_COSTS:,.0f} ₽".replace(",", " "),
                    style={"color": "#E8A838", "margin": "5px 0"}),
        ], style={"flex": "1", "textAlign": "center"}),

        html.Div([
            html.H4(profit_label, style={"color": "#7F8C8D", "margin": "0"}),
            html.H3(f"{profit:,.0f} ₽".replace(",", " "),
                    style={"color": profit_color, "margin": "5px 0"}),
        ], style={"flex": "1", "textAlign": "center"}),

        html.Div([
            html.H4("Маржа", style={"color": "#7F8C8D", "margin": "0"}),
            html.H3(f"{margin:.1f}%",
                    style={"color": profit_color, "margin": "5px 0"}),
        ], style={"flex": "1", "textAlign": "center"}),
    ], style={"display": "flex", "padding": "20px",
              "backgroundColor": "#F8F9FA", "borderRadius": "8px"})


# ─────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Дашборд Surf Coffee")
    print("=" * 60)
    print("Откройте в браузере: http://127.0.0.1:8050")
    print("Остановить: Ctrl+C")
    app.run(debug=False, host="127.0.0.1", port=8050)
