# utils/translations.py
# Dicionario central de traducoes: PT (padrao) → EN → ZH (mandarin simplificado)
# Uso: from utils.i18n import t  →  t("chave")
#
# ATENÇÃO: strings zh (chinês) que precisem de aspas no meio devem usar 「」 em vez de ""
# pois "" dentro de uma string Python delimitada por "" causa SyntaxError.

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
    # RODAPE
    # ─────────────────────────────────────────────
    "rodape.texto": {
        "pt": "© 2026 Samuel Freitas — Torre de Controle. Todos os direitos reservados.",
        "en": "© 2026 Samuel Freitas — Control Tower. All rights reserved.",
        "zh": "© 2026 Samuel Freitas — 控制塔。保留所有权利。",
    },
}
