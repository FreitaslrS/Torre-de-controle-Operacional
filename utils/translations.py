# utils/translations.py
# Dicionario central de traducoes: PT (padrao) → EN → ZH (mandarin simplificado)
# Uso: from utils.i18n import t  →  t("chave")
#
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  ATENÇÃO — regra obrigatória para strings zh (chinês):                   ║
# ║  Aspas dentro do texto devem usar 「」 e nunca ""                         ║
# ║  Exemplo correto:  "zh": "请使用「退货 + 监控」导入。"                   ║
# ║  Exemplo ERRADO:   "zh": "请使用"退货 + 监控"导入。"  ← SyntaxError!    ║
# ║  Para validar o arquivo: python -c "import utils.translations"           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ─────────────────────────────────────────────
    # NAVEGACAO GLOBAL
    # ─────────────────────────────────────────────
    "nav.voltar_home": {
        "pt": "← Home",
        "en": "← Home",
        "zh": "← 首页",
    },
    "nav.sair": {
        "pt": "Sair",
        "en": "Logout",
        "zh": "退出",
    },

    # ─────────────────────────────────────────────
    # HOME
    # ─────────────────────────────────────────────
    "home.titulo": {
        "pt": "Anjun Express — BI de Operações",
        "en": "Anjun Express — Operations BI",
        "zh": "安骏快递 — 运营数据分析",
    },
    "home.subtitulo": {
        "pt": "Selecione um módulo para começar",
        "en": "Select a module to begin",
        "zh": "选择模块以开始",
    },
    # Cards — títulos
    "card.backlog.titulo": {
        "pt": "Backlog Atual",
        "en": "Current Backlog",
        "zh": "当前积压",
    },
    "card.historico.titulo": {
        "pt": "Backlog Histórico",
        "en": "Historical Backlog",
        "zh": "历史积压",
    },
    "card.produtividade.titulo": {
        "pt": "Produtividade",
        "en": "Productivity",
        "zh": "生产力",
    },
    "card.tempo.titulo": {
        "pt": "Tempo",
        "en": "Time",
        "zh": "时间",
    },
    "card.health_check.titulo": {
        "pt": "Health Check",
        "en": "Health Check",
        "zh": "健康检查",
    },
    "card.devolucoes.titulo": {
        "pt": "Devoluções",
        "en": "Returns",
        "zh": "退货",
    },
    "card.coletas.titulo": {
        "pt": "Coletas, Carregamento e Descarregamento",
        "en": "Collections, Loading and Unloading",
        "zh": "收件、装车与卸车",
    },
    "card.coletas.btn": {
        "pt": "Coletas",
        "en": "Collections",
        "zh": "收件",
    },
    "card.importacao.titulo": {
        "pt": "Importação",
        "en": "Import",
        "zh": "数据导入",
    },
    # Cards — subtítulos
    "card.backlog.sub": {
        "pt": "Visão operacional em tempo real",
        "en": "Real-time operational view",
        "zh": "实时运营视图",
    },
    "card.historico.sub": {
        "pt": "Análise e evolução histórica",
        "en": "Analysis and historical evolution",
        "zh": "分析与历史趋势",
    },
    "card.produtividade.sub": {
        "pt": "Volume por turno e dispositivo",
        "en": "Volume by shift and device",
        "zh": "按班次和设备的处理量",
    },
    "card.tempo.sub": {
        "pt": "SLA e tempo de processamento",
        "en": "SLA and processing time",
        "zh": "SLA与处理时间",
    },
    "card.health_check.sub": {
        "pt": "Saúde operacional consolidada",
        "en": "Consolidated operational health",
        "zh": "综合运营健康状况",
    },
    "card.devolucoes.sub": {
        "pt": "Pedidos devolvidos e P90",
        "en": "Returned orders and P90",
        "zh": "退货订单与P90",
    },
    "card.coletas.sub": {
        "pt": "Carregamento e descarregamento",
        "en": "Loading and unloading",
        "zh": "装车与卸车",
    },
    "card.importacao.sub": {
        "pt": "Upload de planilhas",
        "en": "Spreadsheet upload",
        "zh": "上传电子表格",
    },

    # ─────────────────────────────────────────────
    # COMUNS (reutilizados em múltiplas páginas)
    # ─────────────────────────────────────────────
    "comum.sem_dados": {
        "pt": "Sem dados",
        "en": "No data",
        "zh": "暂无数据",
    },
    "comum.sem_dados_periodo": {
        "pt": "Sem dados para o período selecionado.",
        "en": "No data for the selected period.",
        "zh": "所选时段无数据。",
    },
    "comum.sem_dados_filtro": {
        "pt": "Sem dados para o filtro selecionado.",
        "en": "No data for the selected filter.",
        "zh": "所选筛选条件无数据。",
    },
    "comum.sem_dados_semana": {
        "pt": "Sem dados para a semana selecionada.",
        "en": "No data for the selected week.",
        "zh": "所选周无数据。",
    },
    "comum.data_inicio": {
        "pt": "Data início",
        "en": "Start date",
        "zh": "开始日期",
    },
    "comum.data_fim": {
        "pt": "Data fim",
        "en": "End date",
        "zh": "结束日期",
    },
    "comum.data_referencia": {
        "pt": "Data de referência",
        "en": "Reference date",
        "zh": "参考日期",
    },
    "comum.semana": {
        "pt": "Semana",
        "en": "Week",
        "zh": "周",
    },
    "comum.semana_referencia": {
        "pt": "Semana de referência",
        "en": "Reference week",
        "zh": "参考周",
    },
    "comum.todos": {
        "pt": "Todos",
        "en": "All",
        "zh": "全部",
    },
    "comum.nenhuma": {
        "pt": "Nenhuma",
        "en": "None",
        "zh": "无",
    },
    "comum.total": {
        "pt": "Total",
        "en": "Total",
        "zh": "合计",
    },
    "comum.estado": {
        "pt": "Estado",
        "en": "State",
        "zh": "州",
    },
    "comum.cliente": {
        "pt": "Cliente",
        "en": "Client",
        "zh": "客户",
    },
    "comum.turno": {
        "pt": "Turno",
        "en": "Shift",
        "zh": "班次",
    },
    "comum.filtros": {
        "pt": "Filtros",
        "en": "Filters",
        "zh": "筛选器",
    },
    "comum.download": {
        "pt": "Download",
        "en": "Download",
        "zh": "下载",
    },
    "comum.periodo": {
        "pt": "Período",
        "en": "Period",
        "zh": "时段",
    },
    "comum.proximo_ponto": {
        "pt": "Próximo Ponto",
        "en": "Next Point",
        "zh": "下一站",
    },
    "comum.remover_estados": {
        "pt": "Remover Estados",
        "en": "Remove States",
        "zh": "排除州份",
    },
    "comum.remover_clientes": {
        "pt": "Remover Clientes",
        "en": "Remove Clients",
        "zh": "排除客户",
    },
    "comum.filtro_horas": {
        "pt": "Filtro por Horas",
        "en": "Filter by Hours",
        "zh": "按小时筛选",
    },
    "comum.filtro_dias": {
        "pt": "Filtro por Faixa de Dias",
        "en": "Filter by Day Range",
        "zh": "按天数区间筛选",
    },
    "comum.ate_24h": {
        "pt": "Até 24h",
        "en": "Up to 24h",
        "zh": "24小时以内",
    },
    "comum.sem_info": {
        "pt": "Sem informação",
        "en": "No information",
        "zh": "无信息",
    },
    "comum.filtrar_periodo": {
        "pt": "Filtrar por período",
        "en": "Filter by period",
        "zh": "按时段筛选",
    },

    # ─────────────────────────────────────────────
    # BACKLOG ATUAL
    # ─────────────────────────────────────────────
    "backlog.titulo": {
        "pt": "Backlog Atual",
        "en": "Current Backlog",
        "zh": "当前积压",
    },
    "backlog.subtitulo": {
        "pt": "Monitoramento em tempo real da operação",
        "en": "Real-time operation monitoring",
        "zh": "实时运营监控",
    },
    "backlog.critico": {
        "pt": "Backlog crítico!",
        "en": "Critical backlog!",
        "zh": "积压严重！",
    },
    "backlog.atencao": {
        "pt": "Backlog em atenção",
        "en": "Backlog requires attention",
        "zh": "积压需关注",
    },
    "backlog.controlado": {
        "pt": "Operação controlada",
        "en": "Operation under control",
        "zh": "运营正常",
    },
    "backlog.pct_critico": {
        "pt": "% Crítico",
        "en": "% Critical",
        "zh": "% 严重",
    },
    "backlog.distribuicao_geo": {
        "pt": "Distribuição Geográfica",
        "en": "Geographic Distribution",
        "zh": "地理分布",
    },
    "backlog.top10_pre": {
        "pt": "Top 10 Pré-entrega",
        "en": "Top 10 Pre-delivery",
        "zh": "前10预派送点",
    },
    "backlog.por_estado_sla": {
        "pt": "Backlog por Estado (SLA)",
        "en": "Backlog by State (SLA)",
        "zh": "按州积压（SLA）",
    },
    "backlog.download_waybills": {
        "pt": "Download Waybills em Backlog",
        "en": "Download Backlog Waybills",
        "zh": "下载积压运单",
    },
    "backlog.sem_waybill": {
        "pt": "Nenhum waybill disponível (dados expiram após 7 dias).",
        "en": "No waybill available (data expires after 7 days).",
        "zh": "暂无运单（数据7天后过期）。",
    },
    "backlog.geojson_nao_encontrado": {
        "pt": "GeoJSON não encontrado em assets/brasil_estados.json",
        "en": "GeoJSON not found in assets/brasil_estados.json",
        "zh": "地理数据文件未找到",
    },

    # ─────────────────────────────────────────────
    # BACKLOG HISTORICO
    # ─────────────────────────────────────────────
    "historico.titulo": {
        "pt": "Backlog Histórico",
        "en": "Historical Backlog",
        "zh": "历史积压",
    },
    "historico.subtitulo": {
        "pt": "Visão completa histórica da operação",
        "en": "Complete historical view of operation",
        "zh": "运营完整历史视图",
    },
    "historico.total_periodo": {
        "pt": "Total no Período",
        "en": "Total in Period",
        "zh": "时段合计",
    },
    "historico.por_estado_faixa": {
        "pt": "Backlog por Estado (Faixa de Tempo)",
        "en": "Backlog by State (Time Range)",
        "zh": "按州积压（时间段）",
    },

    # ─────────────────────────────────────────────
    # PRODUTIVIDADE
    # ─────────────────────────────────────────────
    "prod.titulo": {
        "pt": "Produtividade",
        "en": "Productivity",
        "zh": "生产力",
    },
    "prod.subtitulo": {
        "pt": "Volume por turno e dispositivo",
        "en": "Volume by shift and device",
        "zh": "按班次和设备的处理量",
    },
    "prod.tab_produtividade": {
        "pt": "Produtividade",
        "en": "Productivity",
        "zh": "生产力",
    },
    "prod.tab_pacotes_grandes": {
        "pt": "Pacotes Grandes",
        "en": "Large Packages",
        "zh": "大件包裹",
    },
    "prod.tab_presenca": {
        "pt": "Presença e Eficiência",
        "en": "Attendance and Efficiency",
        "zh": "出勤与效率",
    },
    "prod.sem_dados_filtros": {
        "pt": "Sem dados após filtros",
        "en": "No data after filters",
        "zh": "筛选后无数据",
    },
    "prod.por_turno": {
        "pt": "Por Turno",
        "en": "By Shift",
        "zh": "按班次",
    },
    "prod.por_dispositivo": {
        "pt": "Por Dispositivo",
        "en": "By Device",
        "zh": "按设备",
    },
    "prod.por_hora": {
        "pt": "Produtividade por Hora (Dispositivos)",
        "en": "Productivity by Hour (Devices)",
        "zh": "按小时生产力（设备）",
    },
    "prod.resumo_hora": {
        "pt": "Resumo por Hora",
        "en": "Summary by Hour",
        "zh": "按小时摘要",
    },
    "prod.top10_clientes": {
        "pt": "Top 10 Clientes",
        "en": "Top 10 Clients",
        "zh": "前10客户",
    },
    "prod.por_cliente": {
        "pt": "Produção por Cliente",
        "en": "Production by Client",
        "zh": "按客户生产量",
    },
    # Pacotes Grandes
    "pg.titulo": {
        "pt": "Pacotes Grandes",
        "en": "Large Packages",
        "zh": "大件包裹",
    },
    "pg.subtitulo": {
        "pt": "Encomendas com prefixo AJG",
        "en": "Parcels with AJG prefix",
        "zh": "带AJG前缀的大件包裹",
    },
    "pg.sem_dados": {
        "pt": "Sem dados. Importe um arquivo do tipo 'Pacotes Grandes'.",
        "en": "No data. Import a file of type 'Large Packages'.",
        "zh": "暂无数据。请导入「大件包裹」类型文件。",
    },
    "pg.total_pacotes": {
        "pt": "Total Pacotes",
        "en": "Total Packages",
        "zh": "包裹总计",
    },
    "pg.peso_medio": {
        "pt": "Peso Médio",
        "en": "Average Weight",
        "zh": "平均重量",
    },
    "pg.volume_medio": {
        "pt": "Volume Médio",
        "en": "Average Volume",
        "zh": "平均体积",
    },
    "pg.entregues": {
        "pt": "Entregues",
        "en": "Delivered",
        "zh": "已派送",
    },
    "pg.por_status": {
        "pt": "Por Status",
        "en": "By Status",
        "zh": "按状态",
    },
    "pg.por_estado": {
        "pt": "Por Estado",
        "en": "By State",
        "zh": "按州",
    },
    "pg.tabela_detalhada": {
        "pt": "Tabela Detalhada",
        "en": "Detailed Table",
        "zh": "详细表格",
    },
    # Presença e Eficiência
    "pres.titulo": {
        "pt": "Presença e Eficiência Operacional",
        "en": "Operational Attendance and Efficiency",
        "zh": "运营出勤与效率",
    },
    "pres.sem_dados": {
        "pt": "Sem dados. Importe a planilha de Presença na página de Importação.",
        "en": "No data. Import the Attendance spreadsheet on the Import page.",
        "zh": "暂无数据。请在导入页面上传出勤表。",
    },
    "pres.produzido_semana": {
        "pt": "Produzido na semana",
        "en": "Produced in the week",
        "zh": "本周处理量",
    },
    "pres.presenca_media": {
        "pt": "Presença média/dia",
        "en": "Avg attendance/day",
        "zh": "日均出勤人数",
    },
    "pres.faltas_anjun": {
        "pt": "Faltas Anjun",
        "en": "Anjun Absences",
        "zh": "安骏缺勤",
    },
    "pres.faltas_temp": {
        "pt": "Faltas Temporários",
        "en": "Temp Absences",
        "zh": "临时工缺勤",
    },
    "pres.absenteismo": {
        "pt": "% Absenteísmo médio",
        "en": "Avg Absenteeism %",
        "zh": "平均缺勤率%",
    },
    "pres.producao_turno": {
        "pt": "Produção por Turno",
        "en": "Production by Shift",
        "zh": "按班次产量",
    },
    "pres.eficiencia_turno": {
        "pt": "Eficiência por Turno (vol/pessoa)",
        "en": "Efficiency by Shift (vol/person)",
        "zh": "班次效率（件/人）",
    },
    "pres.vol_diario_cliente": {
        "pt": "Evolução do Volume Diário por Cliente",
        "en": "Daily Volume Evolution by Client",
        "zh": "按客户日量趋势",
    },
    "pres.custo_diaristas": {
        "pt": "Custo de Diaristas por Dia",
        "en": "Daily Worker Cost by Day",
        "zh": "日工成本（按天）",
    },
    "pres.detalhamento_turno": {
        "pt": "Detalhamento por Turno",
        "en": "Detail by Shift",
        "zh": "班次明细",
    },

    # ─────────────────────────────────────────────
    # TEMPO DE PROCESSAMENTO
    # ─────────────────────────────────────────────
    "tempo.titulo": {
        "pt": "Tempo de Processamento",
        "en": "Processing Time",
        "zh": "处理时间",
    },
    "tempo.subtitulo": {
        "pt": "SLA e tempo entre entrada e saída no hub",
        "en": "SLA and time between hub entry and exit",
        "zh": "枢纽进出SLA与时间",
    },
    "tempo.tab_sla": {
        "pt": "SLA Hub",
        "en": "Hub SLA",
        "zh": "枢纽SLA",
    },
    "tempo.tab_hiata": {
        "pt": "Hiatas H001",
        "en": "Hiatas H001",
        "zh": "H001断层",
    },
    "tempo.tab_consolidado": {
        "pt": "Consolidado Operacional",
        "en": "Operational Consolidated",
        "zh": "运营汇总",
    },
    "tempo.tab_percentis": {
        "pt": "📊 P50 / P80 / P90",
        "en": "📊 P50 / P80 / P90",
        "zh": "📊 P50 / P80 / P90",
    },
    "tempo.percentis_titulo": {
        "pt": "Percentis de Entrega por Estado (Hub → Saída)",
        "en": "Delivery Percentiles by State (Hub → Out)",
        "zh": "各州配送百分位（枢纽→出库）",
    },
    "tempo.p_percentis_por_estado": {
        "pt": "P50 / P80 / P90 por Estado",
        "en": "P50 / P80 / P90 by State",
        "zh": "各州P50/P80/P90",
    },
    "tempo.p50_medio": {
        "pt": "P50 médio",
        "en": "Average P50",
        "zh": "平均P50",
    },
    "tempo.p80_medio": {
        "pt": "P80 médio",
        "en": "Average P80",
        "zh": "平均P80",
    },
    "tempo.p90_medio": {
        "pt": "P90 médio",
        "en": "Average P90",
        "zh": "平均P90",
    },
    "tempo.sla_24h": {
        "pt": "SLA 24h",
        "en": "24h SLA",
        "zh": "24小时SLA",
    },
    "tempo.tempo_medio": {
        "pt": "Tempo médio",
        "en": "Average time",
        "zh": "平均时间",
    },
    "tempo.sla_critico": {
        "pt": "SLA crítico",
        "en": "Critical SLA",
        "zh": "SLA严重不达标",
    },
    "tempo.sla_atencao": {
        "pt": "SLA em atenção",
        "en": "SLA requires attention",
        "zh": "SLA需关注",
    },
    "tempo.sla_saudavel": {
        "pt": "SLA saudável",
        "en": "Healthy SLA",
        "zh": "SLA健康",
    },
    "tempo.media_acima_24h": {
        "pt": "Tempo médio acima de 24h",
        "en": "Average time above 24h",
        "zh": "平均时间超过24小时",
    },
    "tempo.media_dentro_sla": {
        "pt": "Tempo médio dentro do SLA",
        "en": "Average time within SLA",
        "zh": "平均时间在SLA内",
    },
    "tempo.distribuicao_status": {
        "pt": "Distribuição por Status",
        "en": "Distribution by Status",
        "zh": "按状态分布",
    },
    "tempo.evolucao_dia": {
        "pt": "Evolução por Dia",
        "en": "Evolution by Day",
        "zh": "按天趋势",
    },
    "tempo.top5_estados_atraso": {
        "pt": "Top 5 Estados com Maior Atraso",
        "en": "Top 5 States with Most Delays",
        "zh": "前5延误最多州",
    },
    "tempo.top10_pontos_atraso": {
        "pt": "Top 10 Pontos de Entrada com Atraso",
        "en": "Top 10 Entry Points with Delay",
        "zh": "前10延误入境点",
    },
    "tempo.sem_atrasos": {
        "pt": "Sem atrasos nos pontos de entrada",
        "en": "No delays at entry points",
        "zh": "入境点无延误",
    },
    "tempo.por_estado": {
        "pt": "Tempo por Estado",
        "en": "Time by State",
        "zh": "按州时间",
    },
    "tempo.hiata_por_dia": {
        "pt": "Volume de Hiatas H001 por Dia",
        "en": "H001 Hiatas Volume by Day",
        "zh": "H001断层日量",
    },
    "tempo.sem_dados_hiata": {
        "pt": "Sem dados de hiata",
        "en": "No hiata data",
        "zh": "无断层数据",
    },
    "tempo.consolidacao_titulo": {
        "pt": "Consolidação Operacional (Perus + TFK)",
        "en": "Operational Consolidation (Perus + TFK)",
        "zh": "运营汇总（Perus + TFK）",
    },
    "tempo.sem_dados_periodo": {
        "pt": "Sem dados para o período",
        "en": "No data for the period",
        "zh": "该时段无数据",
    },

    # ─────────────────────────────────────────────
    # HEALTH CHECK
    # ─────────────────────────────────────────────
    "hc.titulo": {
        "pt": "Health Check Operacional",
        "en": "Operational Health Check",
        "zh": "运营健康检查",
    },
    "hc.subtitulo": {
        "pt": "Visão consolidada semanal — Performance de SLAs, Backlog e Produtividade",
        "en": "Weekly consolidated view — SLA, Backlog and Productivity performance",
        "zh": "周度汇总视图 — SLA、积压与生产力表现",
    },
    "hc.sem_dados": {
        "pt": "Sem dados. Importe os arquivos de Tempo de Processamento e Produtividade.",
        "en": "No data. Import Processing Time and Productivity files.",
        "zh": "暂无数据。请导入处理时间和生产力文件。",
    },
    "hc.comparar": {
        "pt": "Comparar com outra semana",
        "en": "Compare with another week",
        "zh": "与其他周对比",
    },
    "hc.semana_comparacao": {
        "pt": "Semana de comparação",
        "en": "Comparison week",
        "zh": "对比周",
    },
    "hc.performance_saidas": {
        "pt": "Performance de Saídas e Lead Time",
        "en": "Output Performance and Lead Time",
        "zh": "出件表现与交货期",
    },
    "hc.total_processado": {
        "pt": "Total Processado",
        "en": "Total Processed",
        "zh": "总处理量",
    },
    "hc.dentro_sla": {
        "pt": "Dentro do SLA",
        "en": "Within SLA",
        "zh": "SLA内",
    },
    "hc.lead_time_medio": {
        "pt": "Lead Time Médio",
        "en": "Average Lead Time",
        "zh": "平均交货期",
    },
    "hc.fora_sla": {
        "pt": "Fora do SLA",
        "en": "Outside SLA",
        "zh": "SLA外",
    },
    "hc.backlog_24h": {
        "pt": "Backlog 24h",
        "en": "24h Backlog",
        "zh": "24小时积压",
    },
    "hc.backlog_24h_caption": {
        "pt": "Snapshot atual — pacotes com mais de 24h no hub sem saída",
        "en": "Current snapshot — packages over 24h in hub without exit",
        "zh": "当前快照 — 枢纽内超24小时未出件的包裹",
    },
    "hc.sem_dados_backlog": {
        "pt": "Sem dados de backlog. Importe o arquivo de backlog.",
        "en": "No backlog data. Import the backlog file.",
        "zh": "无积压数据。请导入积压文件。",
    },
    "hc.backlog_48h": {
        "pt": "Backlog 48h",
        "en": "48h Backlog",
        "zh": "48小时积压",
    },
    "hc.backlog_48h_caption": {
        "pt": "Snapshot atual — pacotes com mais de 48h no hub sem saída",
        "en": "Current snapshot — packages over 48h in hub without exit",
        "zh": "当前快照 — 枢纽内超48小时未出件的包裹",
    },
    "hc.sem_dados_backlog_48h": {
        "pt": "Sem dados de backlog 48h.",
        "en": "No 48h backlog data.",
        "zh": "无48小时积压数据。",
    },
    "hc.prod_turno": {
        "pt": "Produtividade por Turno",
        "en": "Productivity by Shift",
        "zh": "按班次生产力",
    },
    "hc.vol_total_processado": {
        "pt": "Volume Total Processado",
        "en": "Total Volume Processed",
        "zh": "总处理量",
    },
    "hc.turno1": {
        "pt": "Turno 1",
        "en": "Shift 1",
        "zh": "第一班",
    },
    "hc.turno2": {
        "pt": "Turno 2",
        "en": "Shift 2",
        "zh": "第二班",
    },
    "hc.turno3": {
        "pt": "Turno 3",
        "en": "Shift 3",
        "zh": "第三班",
    },
    "hc.sem_dados_prod": {
        "pt": "Sem dados de produtividade para esta semana.",
        "en": "No productivity data for this week.",
        "zh": "本周无生产力数据。",
    },

    # ─────────────────────────────────────────────
    # DEVOLUCOES
    # ─────────────────────────────────────────────
    "dev.titulo": {
        "pt": "Devoluções",
        "en": "Returns",
        "zh": "退货",
    },
    "dev.subtitulo": {
        "pt": "Pedidos devolvidos e P90",
        "en": "Returned orders and P90",
        "zh": "退货订单与P90",
    },
    "dev.cliente": {
        "pt": "Cliente",
        "en": "Client",
        "zh": "客户",
    },
    "dev.importar_mon": {
        "pt": "Importe 'Devolução - Monitoramento' para filtrar por cliente",
        "en": "Import 'Return - Monitoring' to filter by client",
        "zh": "导入「退货 - 监控」以按客户筛选",
    },

    # ─────────────────────────────────────────────
    # COLETAS
    # ─────────────────────────────────────────────
    "col.titulo": {
        "pt": "Coletas e Carregamento",
        "en": "Collections and Loading",
        "zh": "收件与装车",
    },
    "col.subtitulo": {
        "pt": "Descarregamento em Perus e carregamentos com saída para outras bases",
        "en": "Unloading in Perus and loads departing to other hubs",
        "zh": "Perus卸车及出件至其他基地",
    },
    "col.tab_desc": {
        "pt": "Descarregamento em Perus",
        "en": "Unloading in Perus",
        "zh": "Perus卸车",
    },
    "col.tab_saida": {
        "pt": "Saída para Bases",
        "en": "Departure to Hubs",
        "zh": "出件至基地",
    },
    "col.sem_dados_desc": {
        "pt": "Sem dados. Importe um arquivo do tipo 'Coletas — Descarregamento em Perus'.",
        "en": "No data. Import a file of type 'Collections — Unloading in Perus'.",
        "zh": "暂无数据。请导入「收件 — Perus卸车」类型文件。",
    },
    "col.sem_dados_saida": {
        "pt": "Sem dados. Importe um arquivo do tipo 'Coletas — Saída para Bases'.",
        "en": "No data. Import a file of type 'Collections — Departure to Hubs'.",
        "zh": "暂无数据。请导入「收件 — 出件至基地」类型文件。",
    },
    "col.sem_registros_desc": {
        "pt": "Sem registros de descarregamento para a data selecionada.",
        "en": "No unloading records for the selected date.",
        "zh": "所选日期无卸车记录。",
    },
    "col.sem_registros_saida": {
        "pt": "Sem registros de saída para a data selecionada.",
        "en": "No departure records for the selected date.",
        "zh": "所选日期无出件记录。",
    },
    "col.veiculos": {
        "pt": "Veículos",
        "en": "Vehicles",
        "zh": "车辆",
    },
    "col.pac_carregados": {
        "pt": "Pacotes Carregados",
        "en": "Loaded Packages",
        "zh": "已装包裹",
    },
    "col.pac_descarregados": {
        "pt": "Pacotes Descarregados",
        "en": "Unloaded Packages",
        "zh": "已卸包裹",
    },
    "col.dif_pacotes": {
        "pt": "Diferença Pacotes",
        "en": "Package Difference",
        "zh": "包裹差异",
    },
    "col.sacos_carregados": {
        "pt": "Sacos Carregados",
        "en": "Loaded Bags",
        "zh": "已装袋数",
    },
    "col.pac_por_origem": {
        "pt": "Pacotes Recebidos por Rede de Origem",
        "en": "Packages Received by Origin Network",
        "zh": "按来源网络收件量",
    },
    "col.dif_por_origem": {
        "pt": "Diferença por Rede de Origem (Carregado vs Descarregado)",
        "en": "Difference by Origin Network (Loaded vs Unloaded)",
        "zh": "按来源网络差异（装车 vs 卸车）",
    },
    "col.timeline_desc": {
        "pt": "Timeline de Descarregamento (por hora)",
        "en": "Unloading Timeline (by hour)",
        "zh": "卸车时间线（按小时）",
    },
    "col.detalhe_veiculo": {
        "pt": "Detalhe por Veículo",
        "en": "Detail by Vehicle",
        "zh": "按车辆明细",
    },
    "col.destinos": {
        "pt": "Destinos",
        "en": "Destinations",
        "zh": "目的地",
    },
    "col.pac_enviados": {
        "pt": "Pacotes Enviados",
        "en": "Packages Sent",
        "zh": "已发包裹",
    },
    "col.sacos_enviados": {
        "pt": "Sacos Enviados",
        "en": "Bags Sent",
        "zh": "已发袋数",
    },
    "col.confirmados_desc": {
        "pt": "Confirmados (Desc.)",
        "en": "Confirmed (Unl.)",
        "zh": "已确认（卸车）",
    },
    "col.vol_por_destino": {
        "pt": "Volume Enviado por Destino (Top 15)",
        "en": "Volume Sent by Destination (Top 15)",
        "zh": "按目的地发件量（前15）",
    },
    "col.dif_por_destino": {
        "pt": "Diferença por Destino (Enviado vs Confirmado)",
        "en": "Difference by Destination (Sent vs Confirmed)",
        "zh": "按目的地差异（发件 vs 确认）",
    },
    "col.timeline_saida": {
        "pt": "Timeline de Carregamento (por hora)",
        "en": "Loading Timeline (by hour)",
        "zh": "装车时间线（按小时）",
    },
    "col.detalhe_veiculo_destino": {
        "pt": "Detalhe por Veículo e Destino",
        "en": "Detail by Vehicle and Destination",
        "zh": "按车辆及目的地明细",
    },
    "col.sem_desc_confirmado": {
        "pt": "Nenhum descarregamento confirmado neste período.",
        "en": "No confirmed unloading in this period.",
        "zh": "本时段无已确认卸车。",
    },

    # ─────────────────────────────────────────────
    # IMPORTACAO
    # ─────────────────────────────────────────────
    "imp.area_restrita": {
        "pt": "Área Restrita",
        "en": "Restricted Area",
        "zh": "限制访问区",
    },
    "imp.acesso_restrito": {
        "pt": "Acesso restrito a usuários autorizados",
        "en": "Access restricted to authorized users",
        "zh": "仅授权用户可访问",
    },
    "imp.senha": {
        "pt": "Senha",
        "en": "Password",
        "zh": "密码",
    },
    "imp.entrar": {
        "pt": "Entrar",
        "en": "Login",
        "zh": "登录",
    },
    "imp.bloqueada_env": {
        "pt": "Importação bloqueada: SENHA_IMPORTACAO não configurada no ambiente.",
        "en": "Import blocked: SENHA_IMPORTACAO not configured in the environment.",
        "zh": "导入已锁定：环境中未配置SENHA_IMPORTACAO。",
    },
    "imp.acesso_bloqueado": {
        "pt": "Acesso bloqueado após {n} tentativas incorretas. Recarregue a página para tentar novamente.",
        "en": "Access blocked after {n} incorrect attempts. Reload the page to try again.",
        "zh": "经过{n}次错误尝试后访问已锁定。请刷新页面重试。",
    },
    "imp.senha_incorreta": {
        "pt": "Senha incorreta. {n} tentativa(s) restante(s).",
        "en": "Wrong password. {n} attempt(s) remaining.",
        "zh": "密码错误。剩余{n}次尝试。",
    },
    "imp.acesso_bloqueado_final": {
        "pt": "Acesso bloqueado. Recarregue a página para tentar novamente.",
        "en": "Access blocked. Reload the page to try again.",
        "zh": "访问已锁定。请刷新页面重试。",
    },
    "imp.titulo": {
        "pt": "Importação de Dados",
        "en": "Data Import",
        "zh": "数据导入",
    },
    "imp.tipo": {
        "pt": "Tipo de Importação",
        "en": "Import Type",
        "zh": "导入类型",
    },
    "imp.btn_importar": {
        "pt": "Importar",
        "en": "Import",
        "zh": "导入",
    },
    "imp.selecione_data": {
        "pt": "Selecione a data de referência",
        "en": "Select the reference date",
        "zh": "请选择参考日期",
    },
    "imp.selecione_arquivos": {
        "pt": "Selecione arquivos",
        "en": "Select files",
        "zh": "请选择文件",
    },
    "imp.processando": {
        "pt": "Processando arquivos...",
        "en": "Processing files...",
        "zh": "正在处理文件...",
    },
    "imp.historico": {
        "pt": "Histórico de Importações",
        "en": "Import History",
        "zh": "导入历史",
    },
    "imp.sem_arquivos": {
        "pt": "Nenhum arquivo importado ainda",
        "en": "No files imported yet",
        "zh": "尚未导入任何文件",
    },
    "imp.zona_perigo": {
        "pt": "Zona de Perigo",
        "en": "Danger Zone",
        "zh": "危险区域",
    },
    "imp.confirmacao_destruicao": {
        "pt": "Tenho certeza que quero fazer isso (modo destruição)",
        "en": "I'm sure I want to do this (destruction mode)",
        "zh": "我确认要执行此操作（破坏模式）",
    },
    "imp.resetar_backlog": {
        "pt": "Resetar Backlog Atual",
        "en": "Reset Current Backlog",
        "zh": "重置当前积压",
    },
    "imp.backlog_zerado": {
        "pt": "Backlog atual zerado!",
        "en": "Current backlog cleared!",
        "zh": "当前积压已清空！",
    },
    "imp.excluir_data": {
        "pt": "Excluir por Data",
        "en": "Delete by Date",
        "zh": "按日期删除",
    },
    "imp.excluir_data_ref": {
        "pt": "Excluir por data de referência",
        "en": "Delete by reference date",
        "zh": "按参考日期删除",
    },
    "imp.limpar_historico": {
        "pt": "Limpar histórico > 30 dias",
        "en": "Clear history > 30 days",
        "zh": "清除30天前的历史",
    },
    "imp.historico_removido": {
        "pt": "Histórico antigo removido!",
        "en": "Old history removed!",
        "zh": "旧历史已清除！",
    },
    "imp.selecione_monitoramento": {
        "pt": "Selecione o arquivo de Monitoramento de Pontualidade",
        "en": "Select the Punctuality Monitoring file",
        "zh": "请选择准时性监控文件",
    },
    "imp.dois_arquivos_info": {
        "pt": "Este tipo requer dois arquivos: o arquivo principal (Folha de Devolução) vai no uploader acima. Selecione o Monitoramento abaixo.",
        "en": "This type requires two files: the main file (Return Sheet) goes in the uploader above. Select the Monitoring file below.",
        "zh": "此类型需要两个文件：主文件（退货表）上传至上方，监控文件在下方选择。",
    },
    "imp.concluida": {
        "pt": "Importação concluída — {n} registros",
        "en": "Import complete — {n} records",
        "zh": "导入完成 — {n}条记录",
    },

    # ─────────────────────────────────────────────
    # COLUNAS COMUNS (tabelas e gráficos)
    # ─────────────────────────────────────────────
    "col.hora": {
        "pt": "Hora", "en": "Hour", "zh": "时间",
    },
    "col.data": {
        "pt": "Data", "en": "Date", "zh": "日期",
    },
    "col.volumes": {
        "pt": "Volumes", "en": "Volumes", "zh": "件数",
    },
    "col.dispositivo": {
        "pt": "Dispositivo", "en": "Device", "zh": "设备",
    },
    "col.cliente": {
        "pt": "Cliente", "en": "Client", "zh": "客户",
    },
    "col.estado": {
        "pt": "Estado", "en": "State", "zh": "州",
    },
    "col.cidade": {
        "pt": "Cidade", "en": "City", "zh": "城市",
    },
    "col.waybill": {
        "pt": "Waybill", "en": "Waybill", "zh": "运单号",
    },
    "col.turno": {
        "pt": "Turno", "en": "Shift", "zh": "班次",
    },
    "col.produzido": {
        "pt": "Produzido", "en": "Produced", "zh": "已处理",
    },
    "col.presenca": {
        "pt": "Presença", "en": "Attendance", "zh": "出勤",
    },
    "col.anjun": {
        "pt": "Anjun", "en": "Anjun", "zh": "安骏",
    },
    "col.temporario": {
        "pt": "Temp.", "en": "Temp.", "zh": "临时工",
    },
    "col.diaristas": {
        "pt": "Diaristas", "en": "Daily Workers", "zh": "日工",
    },
    "col.faltas_anjun": {
        "pt": "Faltas Anjun", "en": "Anjun Absences", "zh": "安骏缺勤",
    },
    "col.faltas_temp": {
        "pt": "Faltas Temp.", "en": "Temp Absences", "zh": "临时工缺勤",
    },
    "col.perc_falta": {
        "pt": "% Falta", "en": "% Absence", "zh": "缺勤率",
    },
    "col.custo_pedido": {
        "pt": "Custo/Pedido", "en": "Cost/Order", "zh": "每单成本",
    },
    "col.custo_diaristas": {
        "pt": "Custo Diaristas", "en": "Daily Worker Cost", "zh": "日工成本",
    },
    "col.placa": {
        "pt": "Placa", "en": "Plate", "zh": "车牌",
    },
    "col.motorista": {
        "pt": "Motorista", "en": "Driver", "zh": "司机",
    },
    "col.estado_origem": {
        "pt": "Estado Origem", "en": "Origin State", "zh": "始发州",
    },
    "col.base_origem": {
        "pt": "Base Origem", "en": "Origin Hub", "zh": "始发站",
    },
    "col.hora_car": {
        "pt": "Hora Car.", "en": "Load Time", "zh": "装货时间",
    },
    "col.descarregado": {
        "pt": "Descarregado?", "en": "Unloaded?", "zh": "已卸货？",
    },
    "col.sacos_car": {
        "pt": "Sacos Car.", "en": "Bags Loaded", "zh": "装袋数",
    },
    "col.sacos_desc": {
        "pt": "Sacos Desc.", "en": "Bags Unloaded", "zh": "卸袋数",
    },
    "col.pac_car": {
        "pt": "Pac. Car.", "en": "Pkgs Loaded", "zh": "装包数",
    },
    "col.pac_desc": {
        "pt": "Pac. Desc.", "en": "Pkgs Unloaded", "zh": "卸包数",
    },
    "col.dif_pac": {
        "pt": "Dif. Pac.", "en": "Pkg Diff.", "zh": "包差",
    },
    "col.destino": {
        "pt": "Destino", "en": "Destination", "zh": "目的地",
    },
    "col.confirmado_desc": {
        "pt": "Confirmado Desc.?", "en": "Unload Confirmed?", "zh": "已确认卸货？",
    },
    "col.pac_enviados": {
        "pt": "Pac. Enviados", "en": "Pkgs Sent", "zh": "发出包数",
    },
    "col.lbl_diferenca": {
        "pt": "Diferença (pacotes)", "en": "Difference (packages)", "zh": "差异（包）",
    },
    "col.lbl_pac_desc": {
        "pt": "Pacotes Descarregados", "en": "Packages Unloaded", "zh": "卸货包数",
    },
    "col.lbl_pac_car": {
        "pt": "Pacotes Carregados", "en": "Packages Loaded", "zh": "装货包数",
    },
    "col.pre_entrega": {
        "pt": "Pré-entrega", "en": "Pre-delivery", "zh": "预派送",
    },
    "col.proximo_ponto": {
        "pt": "Próximo Ponto", "en": "Next Hub", "zh": "下一站",
    },
    "col.tempo_backlog": {
        "pt": "Tempo em Backlog", "en": "Time in Backlog", "zh": "积压时间",
    },
    "col.qtd": {
        "pt": "Qtd", "en": "Qty", "zh": "数量",
    },
    "col.volume": {
        "pt": "Volume", "en": "Volume", "zh": "件量",
    },
    "col.sem_saida": {
        "pt": "Sem Saída", "en": "No Exit", "zh": "无出库",
    },
    "col.media_h": {
        "pt": "Média (h)", "en": "Avg (h)", "zh": "平均（小时）",
    },
    "col.perc_sla": {
        "pt": "% SLA", "en": "% SLA", "zh": "SLA达标率",
    },

    # ─────────────────────────────────────────────
    # PRODUTIVIDADE — colunas/labels
    # ─────────────────────────────────────────────
    "prod.cubometro": {
        "pt": "Cubômetro", "en": "Cubing Machine", "zh": "体积仪",
    },
    "prod.sorter_linear": {
        "pt": "Sorter Linear", "en": "Linear Sorter", "zh": "直线分拣机",
    },
    "prod.sorter_oval": {
        "pt": "Sorter Oval", "en": "Oval Sorter", "zh": "环形分拣机",
    },

    # ─────────────────────────────────────────────
    # TEMPO DE PROCESSAMENTO — labels
    # ─────────────────────────────────────────────
    "tempo.perus": {
        "pt": "Perus", "en": "Perus", "zh": "Perus",
    },
    "tempo.tfk_direto": {
        "pt": "TFK Direto", "en": "TFK Direct", "zh": "TFK直送",
    },

    # ─────────────────────────────────────────────
    # HEALTH CHECK — labels
    # ─────────────────────────────────────────────
    "hc.top5_estados": {
        "pt": "Top 5 Estados", "en": "Top 5 States", "zh": "前5个州",
    },
    "hc.top5_pre": {
        "pt": "Top 5 Pré-entregas", "en": "Top 5 Pre-deliveries", "zh": "前5个预派送",
    },
    "hc.perc_sla": {
        "pt": "% SLA", "en": "% SLA", "zh": "SLA达标率",
    },
    "hc.sla_critico_msg": {
        "pt": "SLA crítico: apenas {p:.1f}% dentro do prazo",
        "en": "Critical SLA: only {p:.1f}% on time",
        "zh": "SLA严重不足：仅 {p:.1f}% 准时",
    },
    "hc.sla_atencao_msg": {
        "pt": "SLA em atenção: {p:.1f}% dentro do prazo",
        "en": "SLA needs attention: {p:.1f}% on time",
        "zh": "SLA需关注：{p:.1f}% 准时",
    },
    "hc.sla_saudavel_msg": {
        "pt": "SLA saudável: {p:.1f}% dentro do prazo",
        "en": "Healthy SLA: {p:.1f}% on time",
        "zh": "SLA健康：{p:.1f}% 准时",
    },
    "hc.status_dentro_prazo": {
        "pt": "Dentro do Prazo ({p:.1f}%)",
        "en": "On Time ({p:.1f}%)",
        "zh": "准时 ({p:.1f}%)",
    },
    "hc.status_fora_prazo": {
        "pt": "Fora do Prazo",
        "en": "Late",
        "zh": "超时",
    },
    "hc.status_sem_saida": {
        "pt": "Sem Saída",
        "en": "No Exit",
        "zh": "无出库",
    },

    # ─────────────────────────────────────────────
    # BACKLOG — labels e colunas
    # ─────────────────────────────────────────────
    "backlog.btn_baixar": {
        "pt": "Baixar {n} waybills",
        "en": "Download {n} waybills",
        "zh": "下载 {n} 运单",
    },
    "backlog.lbl_volume": {
        "pt": "Volume", "en": "Volume", "zh": "件量",
    },

    # ─────────────────────────────────────────────
    # DEVOLUÇÕES — tabs, headers, colunas
    # ─────────────────────────────────────────────
    "dev.tab_resumo": {
        "pt": "📋 Resumo", "en": "📋 Summary", "zh": "📋 摘要",
    },
    "dev.tab_wbr_cliente": {
        "pt": "📊 WBR — Cliente", "en": "📊 WBR — Client", "zh": "📊 WBR — 客户",
    },
    "dev.tab_semanal_interno": {
        "pt": "📊 Semanal — Interno", "en": "📊 Weekly — Internal", "zh": "📊 每周 — 内部",
    },
    "dev.tab_p90": {
        "pt": "🗺️ P90 por Estado (Detalhado)", "en": "🗺️ P90 by State (Detailed)", "zh": "🗺️ 各州P90（详细）",
    },
    "dev.semana_label": {
        "pt": "Semana", "en": "Week", "zh": "周",
    },
    "dev.col_status": {
        "pt": "Status", "en": "Status", "zh": "状态",
    },
    "dev.col_clientes": {
        "pt": "Clientes", "en": "Clients", "zh": "客户数",
    },
    "dev.col_estados": {
        "pt": "Estados", "en": "States", "zh": "州数",
    },
    "dev.col_semana": {
        "pt": "Semana", "en": "Week", "zh": "周",
    },
    "dev.col_ocorrencias": {
        "pt": "Ocorrências", "en": "Occurrences", "zh": "发生次数",
    },
    "dev.col_perc": {
        "pt": "%", "en": "%", "zh": "%",
    },
    "dev.col_prazo": {
        "pt": "Prazo (dias)", "en": "Deadline (days)", "zh": "时限（天）",
    },
    "dev.col_p50": {
        "pt": "P50 (dias)", "en": "P50 (days)", "zh": "P50（天）",
    },
    "dev.col_p80": {
        "pt": "P80 (dias)", "en": "P80 (days)", "zh": "P80（天）",
    },
    "dev.col_p90": {
        "pt": "P90 (dias)", "en": "P90 (days)", "zh": "P90（天）",
    },
    "dev.col_dentro_prazo": {
        "pt": "Dentro do Prazo", "en": "On Time", "zh": "准时",
    },
    "dev.col_fora_prazo": {
        "pt": "Fora do Prazo", "en": "Late", "zh": "超时",
    },
    "dev.col_total_dev": {
        "pt": "Total Dev.", "en": "Total Dev.", "zh": "退货总量",
    },
    "dev.col_perc_no_prazo": {
        "pt": "% no Prazo", "en": "% On Time", "zh": "准时率",
    },
    "dev.sem_dados_semana": {
        "pt": "Sem dados para a semana selecionada.",
        "en": "No data for the selected week.",
        "zh": "所选周无数据。",
    },
    "dev.sla_entregas": {
        "pt": "SLA — Entregas no Prazo", "en": "SLA — On-Time Deliveries", "zh": "SLA — 准时交付",
    },
    "dev.wbr_relatorio": {
        "pt": "📊 WBR — Relatório ao Cliente", "en": "📊 WBR — Client Report", "zh": "📊 WBR — 客户报告",
    },
    "dev.sem_dados_import": {
        "pt": "Sem dados. Importe usando 'Devolução + Monitoramento'.",
        "en": "No data. Import using 'Return + Monitoring'.",
        "zh": "无数据。请使用「退货 + 监控」导入。",
    },
    "dev.sem_dados_mon": {
        "pt": "Sem dados. Importe 'Devolução - Monitoramento'.",
        "en": "No data. Import 'Return - Monitoring'.",
        "zh": "无数据。请导入「退货 - 监控」。",
    },
    "dev.sem_dados_data": {
        "pt": "Sem dados para esta data.",
        "en": "No data for this date.",
        "zh": "此日期无数据。",
    },
    "dev.sem_dados_periodo": {
        "pt": "Sem dados para o período selecionado.",
        "en": "No data for the selected period.",
        "zh": "所选期间无数据。",
    },
    "dev.semana_dev": {
        "pt": "Semana (Devolução)", "en": "Week (Return)", "zh": "周（退货）",
    },
    "dev.data_mon": {
        "pt": "Data (Monitoramento)", "en": "Date (Monitoring)", "zh": "日期（监控）",
    },
    "dev.total_semana": {
        "pt": "Total na semana", "en": "Total this week", "zh": "本周总量",
    },
    "dev.devolvidos": {
        "pt": "Devolvidos", "en": "Returned", "zh": "已退货",
    },
    "dev.retornou_processo": {
        "pt": "Retornou ao Processo", "en": "Returned to Process", "zh": "已重新处理",
    },
    "dev.aguardando": {
        "pt": "Aguardando", "en": "Pending", "zh": "待处理",
    },
    "dev.backlog_status": {
        "pt": "Backlog — Status Atual", "en": "Backlog — Current Status", "zh": "积压 — 当前状态",
    },
    "dev.por_estado": {
        "pt": "Devoluções por Estado", "en": "Returns by State", "zh": "按州退货",
    },
    "dev.motivos_falha": {
        "pt": "Motivos de Falha de Entrega", "en": "Delivery Failure Reasons", "zh": "交付失败原因",
    },
    "dev.principais_motivos": {
        "pt": "Principais Motivos", "en": "Main Reasons", "zh": "主要原因",
    },
    "dev.interceptados_iata": {
        "pt": "Interceptados por Iata", "en": "Intercepted by Hub", "zh": "被站点拦截",
    },
    "dev.principais_estados": {
        "pt": "Principais Estados com Devoluções", "en": "Main States with Returns", "zh": "主要退货州",
    },
    "dev.top5_pre_estado": {
        "pt": "Top 5 Pré-entregas por Estado", "en": "Top 5 Pre-deliveries by State", "zh": "各州前5预派送",
    },
    "dev.dsps_sem3tent": {
        "pt": "DSPs que Devolvem sem 3 Tentativas", "en": "DSPs Returning Without 3 Attempts", "zh": "未满3次尝试退货的DSP",
    },
    "dev.p90_real": {
        "pt": "P90 Real por Estado de Destino", "en": "Real P90 by Destination State", "zh": "各目的地州真实P90",
    },
    "dev.total_proc": {
        "pt": "Total Processado", "en": "Total Processed", "zh": "总处理量",
    },
    "dev.top_motivos": {
        "pt": "Top Motivos de Devolução", "en": "Top Return Reasons", "zh": "退货主因",
    },
    "dev.top_pre_dev": {
        "pt": "Top Pré-entregas com Devolução", "en": "Top Pre-deliveries with Return", "zh": "前N预派送退货",
    },
    "dev.tabela_detalhada": {
        "pt": "Tabela detalhada", "en": "Detailed table", "zh": "详细表格",
    },
    "dev.total_dev_count": {
        "pt": "Total devoluções", "en": "Total returns", "zh": "退货总量",
    },
    "dev.p50_medio": {
        "pt": "P50 médio geral", "en": "Average P50", "zh": "平均P50",
    },
    "dev.p80_medio": {
        "pt": "P80 médio geral", "en": "Average P80", "zh": "平均P80",
    },
    "dev.p90_medio": {
        "pt": "P90 médio geral", "en": "Average P90", "zh": "平均P90",
    },
    "dev.estados_dados": {
        "pt": "Estados com dados", "en": "States with data", "zh": "有数据的州",
    },
    "dev.iata": {
        "pt": "Iata", "en": "Hub", "zh": "站点",
    },
    "dev.categoria": {
        "pt": "Categoria", "en": "Category", "zh": "类别",
    },
    "dev.rel_semanal_interno": {
        "pt": "📊 Relatório Semanal — Interno", "en": "📊 Weekly Report — Internal", "zh": "📊 每周报告 — 内部",
    },

    # ─────────────────────────────────────────────
    # DEV — SHEIN BACKLOG
    # ─────────────────────────────────────────────
    "dev.tab_shein": {
        "pt": "Shein Backlog", "en": "Shein Backlog", "zh": "Shein 退货",
    },
    "dev.shein_sem_dados": {
        "pt": "Nenhum dado Shein importado ainda. Use a importação 「Shein — Backlog Completo」.",
        "en": "No Shein data imported yet. Use the 「Shein — Full Backlog」 import.",
        "zh": "尚未导入 Shein 数据。请使用「Shein — 完整退货」导入。",
    },
    "dev.shein_segmento": {
        "pt": "Segmento", "en": "Segment", "zh": "细分",
    },
    "dev.shein_backlog_ativo": {
        "pt": "Backlog Ativo", "en": "Active Backlog", "zh": "活跃退货量",
    },
    "dev.shein_concluido": {
        "pt": "Concluídos", "en": "Completed", "zh": "已完成",
    },
    "dev.shein_pendente": {
        "pt": "Pendentes", "en": "Pending", "zh": "待处理",
    },
    "dev.shein_sla_pct": {
        "pt": "SLA (%)", "en": "SLA (%)", "zh": "SLA (%)",
    },
    "dev.shein_motivos": {
        "pt": "Motivos de Insucesso", "en": "Failure Reasons", "zh": "失败原因",
    },
    "dev.shein_aging": {
        "pt": "Aging por Segmento", "en": "Aging by Segment", "zh": "按细分的账龄分布",
    },
    "dev.shein_col_aging": {
        "pt": "Faixa de Aging", "en": "Aging Range", "zh": "账龄范围",
    },
    "dev.shein_col_status": {
        "pt": "Status (Folha)", "en": "Status (Sheet)", "zh": "状态（退货表）",
    },
    "dev.shein_data_ref": {
        "pt": "Data de Referência", "en": "Reference Date", "zh": "参考日期",
    },
    "dev.shein_filtro_seg": {
        "pt": "Filtrar por segmento", "en": "Filter by segment", "zh": "按细分筛选",
    },
    "dev.shein_todos_seg": {
        "pt": "Todos", "en": "All", "zh": "全部",
    },

    # ─────────────────────────────────────────────
    # RODAPE
    # ─────────────────────────────────────────────
    "rodape.texto": {
        "pt": "© 2026 Samuel Freitas — Torre de Controle. Todos os direitos reservados.",
        "en": "© 2026 Samuel Freitas — Control Tower. All rights reserved.",
        "zh": "© 2026 Samuel Freitas — 控制塔。保留所有权利。",
    },
}
