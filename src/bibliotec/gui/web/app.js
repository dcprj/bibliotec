/**
 * BiblioTEC Web UI — Script de Controle e Comunicação com o Motor Python
 */

(function () {
  'use strict';

  // --- Estado da Aplicação ---
  const state = {
    sourceDir: '',
    targetDir: '',
    fileOperation: 'copy', // 'copy' | 'move'
    provider: 'gemini',
    recursive: true,
    dryRun: false,
    isRunning: false,
    items: [], // [{ source_path, destination_path, status, stage, message, title, authors, year, grande_area, area_basica, tipo, confidence, used_ocr, sha256, reasoning, error_message }]
    selectedPath: null,
    activeFilter: 'all',
    searchQuery: '',
    activeAreaFilter: null,
  };

  // --- Elementos do DOM ---
  const el = {
    sourcePath: document.getElementById('sourcePathDisplay'),
    targetPath: document.getElementById('targetPathDisplay'),
    btnBrowseSource: document.getElementById('btnBrowseSource'),
    btnBrowseTarget: document.getElementById('btnBrowseTarget'),
    btnOrganize: document.getElementById('btnOrganize'),
    organizeLabel: document.getElementById('organizeLabel'),
    organizeIcon: document.getElementById('organizeIcon'),
    modelSelect: document.getElementById('modelSelect'),
    keyBadge: document.getElementById('keyBadge'),
    keyBadgeText: document.getElementById('keyBadgeText'),
    btnModeCopy: document.getElementById('btnModeCopy'),
    btnModeMove: document.getElementById('btnModeMove'),
    chkRecursive: document.getElementById('chkRecursive'),
    chkDryRun: document.getElementById('chkDryRun'),
    btnPreferences: document.getElementById('btnPreferences'),
    btnCache: document.getElementById('btnCache'),
    
    // Sidebar
    filterList: document.getElementById('statusFilterList'),
    cntTotal: document.getElementById('cntTotal'),
    cntOrganized: document.getElementById('cntOrganized'),
    cntManual: document.getElementById('cntManual'),
    cntDuplicate: document.getElementById('cntDuplicate'),
    cntIgnored: document.getElementById('cntIgnored'),
    cntError: document.getElementById('cntError'),
    capesTree: document.getElementById('capesTree'),

    // Table
    searchInput: document.getElementById('searchInput'),
    btnClearSearch: document.getElementById('btnClearSearch'),
    docTableBody: document.getElementById('docTableBody'),
    tableEmptyState: document.getElementById('tableEmptyState'),

    // Inspector
    inspectorEmpty: document.getElementById('inspectorEmpty'),
    inspectorContent: document.getElementById('inspectorContent'),
    inspStatusBadge: document.getElementById('inspStatusBadge'),
    inspStatusIcon: document.getElementById('inspStatusIcon'),
    inspStatusText: document.getElementById('inspStatusText'),
    inspAbntCard: document.getElementById('inspAbntCard'),
    inspAbntCitation: document.getElementById('inspAbntCitation'),
    btnCopyCitation: document.getElementById('btnCopyCitation'),
    inspTriageCard: document.getElementById('inspTriageCard'),
    inspTriageReason: document.getElementById('inspTriageReason'),
    triageGrandeArea: document.getElementById('triageGrandeArea'),
    triageAreaBasica: document.getElementById('triageAreaBasica'),
    triageTitle: document.getElementById('triageTitle'),
    triageSubtitle: document.getElementById('triageSubtitle'),
    triageAuthors: document.getElementById('triageAuthors'),
    triageYear: document.getElementById('triageYear'),
    triageTipo: document.getElementById('triageTipo'),
    btnApproveTriage: document.getElementById('btnApproveTriage'),
    kvGrandeArea: document.getElementById('kvGrandeArea'),
    kvAreaBasica: document.getElementById('kvAreaBasica'),
    kvTipo: document.getElementById('kvTipo'),
    kvConfianca: document.getElementById('kvConfianca'),
    kvOrigem: document.getElementById('kvOrigem'),
    kvDestino: document.getElementById('kvDestino'),
    kvSha256: document.getElementById('kvSha256'),
    btnOpenPdf: document.getElementById('btnOpenPdf'),
    btnRevealFolder: document.getElementById('btnRevealFolder'),

    // Status bar
    progressBarFill: document.getElementById('progressBarFill'),
    progressPct: document.getElementById('progressPct'),
    stageIndicator: document.getElementById('stageIndicator'),
    countIndicator: document.getElementById('countIndicator'),
    remainingIndicator: document.getElementById('remainingIndicator'),
    qualityMetric: document.getElementById('qualityMetric'),

    // Completion banner
    completionBanner: document.getElementById('completionBanner'),
    bannerHeadline: document.getElementById('bannerHeadline'),
    bannerDetails: document.getElementById('bannerDetails'),
    btnClearBatch: document.getElementById('btnClearBatch'),

    // Completion modal popup
    completionModal: document.getElementById('completionModal'),
    modalTitle: document.getElementById('modalTitle'),
    modalSubtitle: document.getElementById('modalSubtitle'),
    modalIconWrap: document.getElementById('modalIconWrap'),
    modalIconSvg: document.getElementById('modalIconSvg'),
    modalCountOrganized: document.getElementById('modalCountOrganized'),
    modalCountReview: document.getElementById('modalCountReview'),
    modalCountDuplicate: document.getElementById('modalCountDuplicate'),
    modalCountError: document.getElementById('modalCountError'),
    modalQualityBadge: document.getElementById('modalQualityBadge'),
    modalQualityText: document.getElementById('modalQualityText'),
    btnModalClose: document.getElementById('btnModalClose'),
    btnModalReview: document.getElementById('btnModalReview'),
    btnModalClear: document.getElementById('btnModalClear'),

    // About modal dialog
    btnAbout: document.getElementById('btnAbout'),
    aboutModal: document.getElementById('aboutModal'),
    btnAboutClose: document.getElementById('btnAboutClose'),
    btnAboutOk: document.getElementById('btnAboutOk'),
    btnCopyPix: document.getElementById('btnCopyPix'),
    pixKeyInput: document.getElementById('pixKeyInput'),
  };

  // --- Dicionário Taxonômico CAPES/CNPq para o Form de Triagem ---
  const CAPES_TAXONOMY = {
    "Ciências Humanas": ["Psicologia", "Sociologia", "Educação", "História", "Filosofia", "Geografia", "Antropologia", "Ciência Política"],
    "Linguística, Letras e Artes": ["Letras", "Linguística", "Artes", "Música"],
    "Ciências Sociais Aplicadas": ["Direito", "Administração", "Economia", "Comunicação", "Ciência da Informação", "Arquitetura e Urbanismo"],
    "Ciências da Saúde": ["Medicina", "Saúde Coletiva", "Enfermagem", "Farmácia", "Odontologia"],
    "Ciências Exatas e da Terra": ["Ciência da Computação", "Matemática", "Física", "Química", "Geociências"],
    "Engenharias": ["Engenharia de Produção", "Engenharia Elétrica", "Engenharia Civil", "Engenharia Mecânica"],
    "Ciências Biológicas": ["Biologia Geral", "Genética", "Ecologia", "Fisiologia"],
    "Outros": ["Outros"]
  };

  // --- Inicialização do QWebChannel ---
  let backend = null;

  function initWebChannel() {
    if (typeof QWebChannel === 'undefined' || typeof qt === 'undefined' || !qt.webChannelTransport) {
      console.warn('QWebChannel ou qt não disponível — rodando em modo visual simulado.');
      setupMockData();
      return;
    }

    new QWebChannel(qt.webChannelTransport, function (channel) {
      backend = channel.objects.backend;
      window.backend = backend;
      console.log('QWebChannel conectado com sucesso ao backend Python!');

      // Sinais vindos do Python
      backend.pipelineEvent.connect(handlePipelineEvent);
      backend.pipelineFinished.connect(handlePipelineFinished);
      backend.sourceChanged.connect(function (path) { setSource(path); });
      backend.targetChanged.connect(function (path) { setTarget(path); });
      backend.keyStatusChanged.connect(function (hasKey) {
        if (backend && backend.checkProviderKey && state.provider) {
          backend.checkProviderKey(state.provider).then(updateKeyBadge);
        } else {
          updateKeyBadge(hasKey);
        }
      });

      // Obter estado inicial
      backend.getInitialState().then(function (initStateJson) {
        if (!initStateJson) return;
        const init = JSON.parse(initStateJson);
        if (init.source) setSource(init.source);
        if (init.target) setTarget(init.target);
        if (init.provider) {
          el.modelSelect.value = init.provider;
          state.provider = init.provider;
        }
        if (backend.checkProviderKey) {
          backend.checkProviderKey(state.provider).then(updateKeyBadge);
        } else if (init.hasKey !== undefined) {
          updateKeyBadge(init.hasKey);
        }
      });
    });
  }

  // --- Handlers de Eventos do Pipeline (Tempo Real) ---
  function handlePipelineEvent(eventJson) {
    try {
      const ev = typeof eventJson === 'string' ? JSON.parse(eventJson) : eventJson;
      if (!ev) return;

      // Atualizar barra de progresso inferior
      if (ev.total_files && ev.completed_files !== undefined) {
        const pct = Math.round((ev.completed_files / ev.total_files) * 100);
        el.progressBarFill.style.width = pct + '%';
        el.progressPct.textContent = pct + '%';
        el.countIndicator.textContent = ev.completed_files + ' / ' + ev.total_files + ' processados';
        el.remainingIndicator.textContent = 'Restam: ' + (ev.total_files - ev.completed_files);
      }
      if (ev.stage) {
        el.stageIndicator.textContent = 'Estágio: ' + formatStageName(ev.stage);
      }

      // Filtrar eventos de diretório / ciclo de vida
      if (ev.stage === 'scanner' && (ev.status === 'completed' || (ev.message && (ev.message.startsWith('Varredura') || ev.message.includes('PDF(s)'))))) {
        return;
      }
      if (ev.stage === 'pipeline' && ev.status === 'completed') {
        return;
      }
      if (!ev.source_path) return;

      upsertItemFromEvent(ev);
    } catch (err) {
      console.error('[BiblioTEC] Erro ao processar evento:', err, eventJson);
    }
  }

  function handlePipelineFinished(summaryJson) {
    try {
      state.isRunning = false;
      updateOrganizeButton();

      if (!summaryJson) return;
      const summary = typeof summaryJson === 'string' ? JSON.parse(summaryJson) : summaryJson;

      if (summary.error) {
        alert('Erro no processamento do acervo:\n\n' + summary.error);
        return;
      }

      el.progressBarFill.style.width = '100%';
      el.progressPct.textContent = '100%';
      el.stageIndicator.textContent = 'Estágio: Concluído';

      // Métrica de qualidade
      if (summary.manual_review_ratio !== undefined) {
        const ratioPct = (summary.manual_review_ratio * 100).toFixed(1);
        const isOverCeiling = summary.exceeded_manual_review_ceiling;
        el.qualityMetric.className = 'quality-metric ' + (isOverCeiling ? 'badge-red' : 'badge-green');
        el.qualityMetric.textContent = 'Revisão Manual: ' + ratioPct + '% (' + (isOverCeiling ? 'acima' : 'dentro') + ' do teto <= 20%)';
      }

      // Exibir banner informativo de conclusão
      if (el.completionBanner) {
        const org = summary.organized_count || 0;
        const rev = summary.manual_review_count || 0;
        const dup = summary.duplicate_skipped_count || 0;
        const err = summary.error_count || 0;
        el.bannerHeadline.textContent = summary.was_cancelled
          ? 'Processamento interrompido pelo usuário.'
          : 'Organização do lote concluída com sucesso!';
        el.bannerDetails.textContent = `${org} organizado(s) • ${rev} revisão manual • ${dup} duplicata(s) • ${err} erro(s). Clique aqui para limpar e iniciar novo lote.`;
        el.completionBanner.style.display = 'block';
      }

      // Abrir Modal Popup em destaque
      openCompletionModal(summary);

      // Selecionar o primeiro item automaticamente se nada estiver selecionado
      if (state.items.length > 0 && !state.selectedPath) {
        selectItem(state.items[0].source_path);
      }
    } catch (err) {
      console.error('[BiblioTEC] Erro ao finalizar pipeline:', err, summaryJson);
    }
  }

  // --- Modal Popup de Conclusão ---
  function openCompletionModal(summary) {
    if (!el.completionModal) return;

    const org = summary.organized_count || 0;
    const rev = summary.manual_review_count || 0;
    const dup = summary.duplicate_skipped_count || 0;
    const err = summary.error_count || 0;

    if (el.modalCountOrganized) el.modalCountOrganized.textContent = String(org);
    if (el.modalCountReview) el.modalCountReview.textContent = String(rev);
    if (el.modalCountDuplicate) el.modalCountDuplicate.textContent = String(dup);
    if (el.modalCountError) el.modalCountError.textContent = String(err);

    if (summary.was_cancelled) {
      if (el.modalIconWrap) el.modalIconWrap.className = 'modal-icon-wrap icon-warn';
      if (el.modalIconSvg) {
        el.modalIconSvg.innerHTML = '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>';
      }
      if (el.modalTitle) el.modalTitle.textContent = 'Processamento Interrompido';
      if (el.modalSubtitle) el.modalSubtitle.textContent = 'A organização do acervo foi interrompida pelo usuário antes da conclusão total.';
    } else if (err > 0 && org === 0) {
      if (el.modalIconWrap) el.modalIconWrap.className = 'modal-icon-wrap icon-error';
      if (el.modalIconSvg) {
        el.modalIconSvg.innerHTML = '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>';
      }
      if (el.modalTitle) el.modalTitle.textContent = 'Atenção: Erros no Processamento';
      if (el.modalSubtitle) el.modalSubtitle.textContent = 'Ocorreram falhas durante o processamento do lote. Verifique as mensagens de erro na tabela.';
    } else {
      if (el.modalIconWrap) el.modalIconWrap.className = 'modal-icon-wrap icon-success';
      if (el.modalIconSvg) {
        el.modalIconSvg.innerHTML = '<polyline points="20 6 9 17 4 12"></polyline>';
      }
      if (el.modalTitle) el.modalTitle.textContent = 'Organização Concluída com Sucesso!';
      if (el.modalSubtitle) el.modalSubtitle.textContent = 'O lote de documentos foi processado e catalogado conforme as diretrizes CAPES/CNPq.';
    }

    if (summary.manual_review_ratio !== undefined) {
      const ratioPct = (summary.manual_review_ratio * 100).toFixed(1);
      const isOverCeiling = summary.exceeded_manual_review_ceiling;
      if (el.modalQualityBadge) {
        el.modalQualityBadge.className = 'modal-quality-badge ' + (isOverCeiling ? 'badge-red' : 'badge-green');
        el.modalQualityBadge.style.display = 'inline-flex';
      }
      if (el.modalQualityText) {
        el.modalQualityText.textContent = `Taxa de Revisão Manual: ${ratioPct}% (${isOverCeiling ? 'acima' : 'dentro'} do teto ≤ 20%)`;
      }
    } else if (el.modalQualityBadge) {
      el.modalQualityBadge.style.display = 'none';
    }

    el.completionModal.style.display = 'flex';
  }

  function closeCompletionModal() {
    if (el.completionModal) {
      el.completionModal.style.display = 'none';
    }
  }

  window.handlePipelineEvent = handlePipelineEvent;
  window.handlePipelineFinished = handlePipelineFinished;

  function formatStageName(stage) {
    const map = {
      scanner: 'Scanner',
      cache: 'Cache',
      extractor: 'Extração de Texto',
      enricher: 'Enriquecimento',
      llm: 'Classificação LLM',
      organizer: 'Materialização',
      pipeline: 'Concluído'
    };
    return map[stage] || stage;
  }

  // --- Upsert de Item na Grade ---
  function upsertItemFromEvent(ev) {
    if (!ev || !ev.source_path) return;
    if (ev.source_path === state.sourceDir || ev.source_path === state.targetDir) return;

    let item = state.items.find(i => i.source_path === ev.source_path);
    const isNew = !item;

    if (isNew) {
      item = {
        source_path: ev.source_path,
        destination_path: '',
        sha256: '',
        status: 'processing',
        stage: ev.stage,
        message: ev.message,
        title: '',
        subtitle: '',
        authors: [],
        year: null,
        grande_area: '',
        area_basica: '',
        tipo: '',
        confidence: 0,
        used_ocr: false,
        reasoning: '',
        error_message: '',
      };
      state.items.push(item);
    }

    item.stage = ev.stage;
    item.message = ev.message;

    // Atualizar classificação parcial ou completa
    if (ev.classification) {
      const cls = ev.classification;
      item.title = cls.title || item.title;
      item.subtitle = cls.subtitle || item.subtitle;
      item.authors = cls.authors || item.authors;
      item.year = cls.year !== undefined ? cls.year : item.year;
      item.grande_area = cls.grande_area || item.grande_area;
      item.area_basica = cls.area_basica || item.area_basica;
      item.tipo = cls.tipo || item.tipo;
      item.confidence = cls.confidence_score !== undefined ? cls.confidence_score : item.confidence;
      item.used_ocr = cls.used_ocr !== undefined ? cls.used_ocr : item.used_ocr;
      item.reasoning = cls.reasoning || item.reasoning;
      item.publisher = cls.publisher || item.publisher || '';
      item.city = cls.city || item.city || '';
      item.edition = cls.edition || item.edition || '';
      item.journal_name = cls.journal_name || item.journal_name || '';
      item.volume = cls.volume || item.volume || '';
      item.number = cls.number || item.number || '';
      item.pages = cls.pages || item.pages || '';
      item.doi = cls.doi || item.doi || '';
      item.isbn = cls.isbn || item.isbn || '';
    }

    if (ev.destination_path) {
      item.destination_path = ev.destination_path;
    }
    if (ev.sha256) {
      item.sha256 = ev.sha256;
    }

    // Status final
    const terminalStatuses = ['organized', 'manual_review', 'duplicate_skipped', 'ignored_non_pdf', 'error'];
    if (terminalStatuses.includes(ev.status)) {
      item.status = ev.status;
    } else if (ev.status === 'ignored') {
      item.status = 'ignored_non_pdf';
    }

    updateCounters();
    updateTaxonomyTree();
    renderTable();

    // Se o item selecionado foi atualizado, re-renderizar inspetor
    if (state.selectedPath === item.source_path) {
      renderInspector(item);
    }
  }

  // --- Atualização de Contadores ---
  function updateCounters() {
    const counts = {
      total: state.items.length,
      organized: state.items.filter(i => i.status === 'organized').length,
      manual_review: state.items.filter(i => i.status === 'manual_review').length,
      duplicate_skipped: state.items.filter(i => i.status === 'duplicate_skipped').length,
      ignored_non_pdf: state.items.filter(i => i.status === 'ignored_non_pdf').length,
      error: state.items.filter(i => i.status === 'error').length,
    };

    el.cntTotal.textContent = counts.total;
    el.cntOrganized.textContent = counts.organized;
    el.cntManual.textContent = counts.manual_review;
    el.cntDuplicate.textContent = counts.duplicate_skipped;
    el.cntIgnored.textContent = counts.ignored_non_pdf;
    el.cntError.textContent = counts.error;
  }

  // --- Atualização da Árvore CAPES/CNPq ---
  function updateTaxonomyTree() {
    const tree = {};
    for (const it of state.items) {
      if (!it.grande_area) continue;
      if (!tree[it.grande_area]) tree[it.grande_area] = {};
      const area = it.area_basica || 'Geral';
      if (!tree[it.grande_area][area]) tree[it.grande_area][area] = 0;
      tree[it.grande_area][area]++;
    }

    const gAreas = Object.keys(tree).sort();
    if (gAreas.length === 0) {
      el.capesTree.innerHTML = '<div class="tree-empty">Nenhuma área classificada ainda</div>';
      return;
    }

    let html = '';
    for (const ga of gAreas) {
      const isSelected = state.activeAreaFilter === ga;
      html += `<div class="tree-node">
        <div class="tree-header ${isSelected ? 'selected' : ''}" data-area="${escapeHtml(ga)}">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
          <strong>${escapeHtml(ga)}</strong>
        </div>
        <div class="tree-children">`;

      for (const [ab, count] of Object.entries(tree[ga])) {
        const isAbSelected = state.activeAreaFilter === ab;
        html += `<div class="tree-header ${isAbSelected ? 'selected' : ''}" data-area="${escapeHtml(ab)}">
          <span style="color: var(--text-muted);">&bull;</span>
          <span>${escapeHtml(ab)}</span>
          <span class="count-pill badge-gray" style="margin-left: auto;">${count}</span>
        </div>`;
      }
      html += `</div></div>`;
    }
    el.capesTree.innerHTML = html;

    // Eventos de clique na árvore
    el.capesTree.querySelectorAll('.tree-header').forEach(hdr => {
      hdr.addEventListener('click', () => {
        const area = hdr.getAttribute('data-area');
        if (state.activeAreaFilter === area) {
          state.activeAreaFilter = null; // Toggle off
        } else {
          state.activeAreaFilter = area;
        }
        updateTaxonomyTree();
        renderTable();
      });
    });
  }

  // --- Renderização da Tabela de Documentos ---
  function renderTable() {
    const query = state.searchQuery.trim().toLowerCase();
    const filter = state.activeFilter;
    const areaFilter = state.activeAreaFilter;

    const filtered = state.items.filter(item => {
      // Filtro de status da sidebar
      if (filter !== 'all' && item.status !== filter) return false;

      // Filtro da árvore CAPES
      if (areaFilter && item.grande_area !== areaFilter && item.area_basica !== areaFilter) return false;

      // Filtro de busca textual
      if (query) {
        const titleMatch = (item.title || getFilename(item.source_path)).toLowerCase().includes(query);
        const authorsMatch = (item.authors || []).join(' ').toLowerCase().includes(query);
        const yearMatch = (item.year ? String(item.year) : '').includes(query);
        const areaMatch = (item.grande_area + ' ' + item.area_basica).toLowerCase().includes(query);
        const typeMatch = (item.tipo || '').toLowerCase().includes(query);
        const fileMatch = item.source_path.toLowerCase().includes(query);
        if (!titleMatch && !authorsMatch && !yearMatch && !areaMatch && !typeMatch && !fileMatch) {
          return false;
        }
      }

      return true;
    });

    if (filtered.length === 0) {
      el.docTableBody.innerHTML = '';
      el.tableEmptyState.style.display = 'flex';
      el.tableEmptyState.innerHTML = state.items.length === 0
        ? '<p>Nenhum documento no lote. Selecione a pasta de origem e clique em <strong>Organizar Acervo</strong>.</p>'
        : '<p>Nenhum documento encontrado para o filtro ativo.</p>';
      return;
    }

    el.tableEmptyState.style.display = 'none';

    let html = '';
    for (const it of filtered) {
      const isSelected = state.selectedPath === it.source_path;
      const displayTitle = it.title || getFilename(it.source_path);
      const authorsStr = (it.authors && it.authors.length > 0) ? it.authors.join('; ') : '—';
      const yearStr = it.year ? String(it.year) : 's.d.';
      const areaStr = it.grande_area ? (it.grande_area + (it.area_basica ? ' › ' + it.area_basica : '')) : '—';
      const typeStr = it.tipo || '—';
      const confStr = it.confidence ? it.confidence.toFixed(2) : '—';

      html += `<tr class="${isSelected ? 'selected' : ''}" data-path="${escapeHtml(it.source_path)}">
        <td class="col-status">${renderStatusPill(it.status)}</td>
        <td class="col-title" title="${escapeHtml(displayTitle)}"><strong>${escapeHtml(displayTitle)}</strong></td>
        <td class="col-authors" title="${escapeHtml(authorsStr)}">${escapeHtml(authorsStr)}</td>
        <td class="col-year">${escapeHtml(yearStr)}</td>
        <td class="col-area" title="${escapeHtml(areaStr)}">${escapeHtml(areaStr)}</td>
        <td class="col-type">${escapeHtml(typeStr)}</td>
        <td class="col-confidence">${escapeHtml(confStr)}</td>
      </tr>`;
    }

    el.docTableBody.innerHTML = html;

    // Adicionar eventos de clique nas linhas
    el.docTableBody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => {
        const path = row.getAttribute('data-path');
        selectItem(path);
      });
    });
  }

  // --- Renderizador de Pill Badges Semânticos ---
  function renderStatusPill(status) {
    switch (status) {
      case 'organized':
        return `<span class="status-pill pill-organized">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          Organizado
        </span>`;
      case 'manual_review':
        return `<span class="status-pill pill-review">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          Revisão
        </span>`;
      case 'duplicate_skipped':
        return `<span class="status-pill pill-duplicate">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          Duplicata
        </span>`;
      case 'processing':
        return `<span class="status-pill pill-processing">
          <svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
          Processando
        </span>`;
      case 'ignored_non_pdf':
        return `<span class="status-pill pill-ignored">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>
          Ignorado
        </span>`;
      case 'error':
        return `<span class="status-pill pill-error">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
          Erro
        </span>`;
      default:
        return `<span class="status-pill pill-processing">${escapeHtml(status || 'Pendente')}</span>`;
    }
  }

  // --- Seleção de Item & Renderização do Inspetor ---
  function selectItem(path) {
    state.selectedPath = path;
    const item = state.items.find(i => i.source_path === path);

    // Destacar linha na tabela
    el.docTableBody.querySelectorAll('tr').forEach(r => {
      r.classList.toggle('selected', r.getAttribute('data-path') === path);
    });

    if (!item) {
      el.inspectorEmpty.style.display = 'flex';
      el.inspectorContent.style.display = 'none';
      return;
    }

    renderInspector(item);
  }

  function renderInspector(item) {
    el.inspectorEmpty.style.display = 'none';
    el.inspectorContent.style.display = 'flex';

    // Badge do topo do Inspetor
    const confPct = Math.round((item.confidence || 0) * 100);
    if (item.status === 'organized') {
      el.inspStatusBadge.className = 'status-pill-lg pill-organized';
      el.inspStatusIcon.textContent = '✔';
      el.inspStatusText.textContent = `Organizado (${confPct}% Confiança)`;
      el.inspAbntCard.style.display = 'block';
      el.inspTriageCard.style.display = 'none';
    } else if (item.status === 'manual_review' || item.status === 'error') {
      el.inspStatusBadge.className = 'status-pill-lg pill-review';
      el.inspStatusIcon.textContent = '⚠';
      el.inspStatusText.textContent = item.status === 'error' ? 'Erro de Processamento' : 'Pendente de Revisão Manual';
      el.inspAbntCard.style.display = 'none';
      el.inspTriageCard.style.display = 'block';
      populateTriageForm(item);
    } else {
      el.inspStatusBadge.className = 'status-pill-lg pill-duplicate';
      el.inspStatusIcon.textContent = '⧉';
      el.inspStatusText.textContent = item.status === 'duplicate_skipped' ? 'Duplicata Exata' : 'Documento Ignorado';
      el.inspAbntCard.style.display = 'none';
      el.inspTriageCard.style.display = 'none';
    }

    // Citação ABNT NBR 6023
    const citation = buildAbntCitation(item);
    el.inspAbntCitation.innerHTML = citation;

    // Metadados CAPES/CNPq
    el.kvGrandeArea.textContent = item.grande_area || '—';
    el.kvAreaBasica.textContent = item.area_basica || '—';
    el.kvTipo.textContent = item.tipo || '—';
    el.kvConfianca.textContent = item.confidence ? `${(item.confidence * 100).toFixed(0)}%` : '—';
    el.kvOrigem.textContent = getFilename(item.source_path);
    el.kvOrigem.title = item.source_path;
    el.kvDestino.textContent = item.destination_path ? getFilename(item.destination_path) : '—';
    el.kvDestino.title = item.destination_path || '';
    el.kvSha256.textContent = item.sha256 ? item.sha256.substring(0, 16) + '...' : '—';
    el.kvSha256.title = item.sha256 || '';

    // Tooltips e contexto dos botões de ação (priorizando destino)
    if (item.destination_path) {
      el.btnOpenPdf.title = `Abrir PDF organizado (${getFilename(item.destination_path)})`;
      el.btnRevealFolder.title = 'Revelar pasta de destino no Finder / Gerenciador de Arquivos';
    } else {
      el.btnOpenPdf.title = 'Abrir PDF de origem no leitor padrão';
      el.btnRevealFolder.title = 'Revelar pasta de origem no Finder / Gerenciador de Arquivos';
    }
  }

  // --- Formulário de Triagem Manual ---
  function populateTriageForm(item) {
    el.inspTriageReason.textContent = item.error_message || item.reasoning || 'Encaminhado para validação humana.';

    // Popular Grande Área
    el.triageGrandeArea.innerHTML = Object.keys(CAPES_TAXONOMY)
      .map(ga => `<option value="${ga}" ${ga === item.grande_area ? 'selected' : ''}>${ga}</option>`)
      .join('');

    updateTriageAreaBasica();

    el.triageTitle.value = item.title || getFilename(item.source_path).replace(/\.pdf$/i, '');
    el.triageSubtitle.value = item.subtitle || '';
    el.triageAuthors.value = (item.authors || []).join('; ');
    el.triageYear.value = item.year || '';
    if (item.tipo) el.triageTipo.value = item.tipo;
  }

  function updateTriageAreaBasica() {
    const selectedGa = el.triageGrandeArea.value;
    const areas = CAPES_TAXONOMY[selectedGa] || ['Outros'];
    el.triageAreaBasica.innerHTML = areas.map(ab => `<option value="${ab}">${ab}</option>`).join('');
  }

  el.triageGrandeArea.addEventListener('change', updateTriageAreaBasica);

  el.btnApproveTriage.addEventListener('click', () => {
    if (!state.selectedPath) return;
    const triageData = {
      source_path: state.selectedPath,
      grande_area: el.triageGrandeArea.value,
      area_basica: el.triageAreaBasica.value,
      tipo: el.triageTipo.value,
      title: el.triageTitle.value.trim(),
      subtitle: el.triageSubtitle.value.trim(),
      authors: el.triageAuthors.value.split(';').map(s => s.trim()).filter(Boolean),
      year: el.triageYear.value ? parseInt(el.triageYear.value, 10) : null,
    };

    if (backend && backend.approveManualTriage) {
      backend.approveManualTriage(JSON.stringify(triageData)).then(res => {
        console.log('Triagem manual aprovada com sucesso!', res);
      });
    } else {
      // Simulação local
      const item = state.items.find(i => i.source_path === state.selectedPath);
      if (item) {
        Object.assign(item, triageData, { status: 'organized', confidence: 1.0 });
        updateCounters();
        updateTaxonomyTree();
        renderTable();
        renderInspector(item);
      }
    }
  });

  // --- Citação ABNT NBR 6023 Completa ---
  function formatAbntAuthors(authors) {
    if (!authors || authors.length === 0) return '';
    const formatted = authors.map(a => {
      a = a.trim();
      if (!a) return '';
      if (a.includes(',')) {
        const parts = a.split(',');
        return `${parts[0].trim().toUpperCase()}, ${parts[1].trim()}`;
      }
      const parts = a.split(' ');
      if (parts.length === 1) return parts[0].toUpperCase();
      const last = parts[parts.length - 1].toUpperCase();
      const first = parts.slice(0, -1).join(' ');
      return `${last}, ${first}`;
    }).filter(Boolean);

    if (formatted.length === 0) return '';
    if (formatted.length === 1) return formatted[0];
    if (formatted.length === 2) return `${formatted[0]}; ${formatted[1]}`;
    if (formatted.length === 3) return `${formatted[0]}; ${formatted[1]}; ${formatted[2]}`;
    return `${formatted[0]} et al.`;
  }

  function buildAbntCitation(item) {
    const authors = formatAbntAuthors(item.authors);
    const title = (item.title || getFilename(item.source_path)).trim();
    const subtitle = item.subtitle ? `: ${item.subtitle.trim()}` : '';
    const edition = item.edition ? `${String(item.edition).replace(/\.+$/, '')}. ed.` : '';
    const city = item.city || '';
    const publisher = item.publisher || '';
    const journalName = item.journal_name || '';
    const volume = item.volume || '';
    const number = item.number || '';
    const year = item.year ? String(item.year) : 's.d.';
    const pages = item.pages ? (String(item.pages).match(/^\d+$/) ? `${item.pages} p.` : item.pages) : '';
    const doi = item.doi ? (String(item.doi).startsWith('http') ? String(item.doi) : `https://doi.org/${item.doi}`) : '';
    const isbn = item.isbn ? String(item.isbn) : '';
    const tipo = item.tipo || '';

    let parts = [];
    if (authors) {
      parts.push(`<strong>${escapeHtml(authors)}</strong>`);
    }

    if (tipo === 'Artigo' && journalName) {
      // Artigo: Título normal, Periódico em negrito
      const artTitle = `${escapeHtml(title)}${escapeHtml(subtitle)}`;
      parts.push(artTitle);

      let jParts = [`<em><strong>${escapeHtml(journalName)}</strong></em>`];
      if (city) jParts.push(escapeHtml(city));
      if (volume) {
        const vStr = String(volume).toLowerCase().startsWith('v.') ? volume : `v. ${volume}`;
        jParts.push(escapeHtml(vStr));
      }
      if (number) {
        const nStr = String(number).toLowerCase().startsWith('n.') ? number : `n. ${number}`;
        jParts.push(escapeHtml(nStr));
      }
      if (pages) {
        const pStr = String(pages).toLowerCase().startsWith('p.') ? pages : `p. ${pages}`;
        jParts.push(escapeHtml(pStr));
      }
      jParts.push(escapeHtml(year));
      parts.push(jParts.join(', '));
    } else {
      // Livro ou Outros: Título em negrito
      const bookTitle = `<em><strong>${escapeHtml(title)}</strong></em>${escapeHtml(subtitle)}`;
      parts.push(bookTitle);

      if (edition) parts.push(escapeHtml(edition));

      // Cidade : Editora, Ano
      let imprint = '';
      if (city && publisher) {
        imprint = `${city}: ${publisher}`;
      } else if (publisher) {
        imprint = `[S.l.]: ${publisher}`;
      } else if (city) {
        imprint = `${city}: [s.n.]`;
      }

      if (imprint) {
        imprint += `, ${year}`;
      } else {
        imprint = year;
      }
      parts.push(escapeHtml(imprint));

      if (pages) parts.push(escapeHtml(pages));
    }

    // Limpar pontos e juntar
    const cleanParts = parts.map(p => p.trim().replace(/\.+$/, '')).filter(Boolean);
    let citation = cleanParts.join('. ') + '.';
    if (doi) citation += ` Disponível em: <a href="${escapeHtml(doi)}" target="_blank">${escapeHtml(doi)}</a>.`;
    if (isbn) citation += ` ISBN ${escapeHtml(isbn)}.`;

    return citation;
  }

  el.btnCopyCitation.addEventListener('click', () => {
    const text = el.inspAbntCitation.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const orig = el.btnCopyCitation.innerHTML;
      el.btnCopyCitation.innerHTML = '✔ Copiado!';
      setTimeout(() => { el.btnCopyCitation.innerHTML = orig; }, 1800);
    });
  });

  // --- Controles de Operação & Ações ---
  el.btnBrowseSource.addEventListener('click', () => {
    if (backend && backend.browseSource) {
      backend.browseSource().then(path => { if (path) setSource(path); });
    }
  });

  el.btnBrowseTarget.addEventListener('click', () => {
    if (backend && backend.browseTarget) {
      backend.browseTarget().then(path => { if (path) setTarget(path); });
    }
  });

  function setSource(path) {
    state.sourceDir = path;
    el.sourcePath.textContent = path || '—';
    el.sourcePath.title = path || '';
  }

  function setTarget(path) {
    state.targetDir = path;
    el.targetPath.textContent = path || '—';
    el.targetPath.title = path || '';
  }

  function updateKeyBadge(hasKey) {
    if (hasKey) {
      el.keyBadge.className = 'badge-pill badge-key-active';
      el.keyBadgeText.textContent = 'Chave Ativa';
    } else {
      el.keyBadge.className = 'badge-pill badge-key-simulated';
      el.keyBadgeText.textContent = 'Sem chave (Modo Simulado)';
    }
  }

  // Segmented Mode (Copiar / Mover)
  el.btnModeCopy.addEventListener('click', () => {
    state.fileOperation = 'copy';
    el.btnModeCopy.classList.add('active');
    el.btnModeMove.classList.remove('active');
  });

  el.btnModeMove.addEventListener('click', () => {
    state.fileOperation = 'move';
    el.btnModeMove.classList.add('active');
    el.btnModeCopy.classList.remove('active');
  });

  // Checkboxes
  el.chkRecursive.addEventListener('change', e => { state.recursive = e.target.checked; });
  el.chkDryRun.addEventListener('change', e => { state.dryRun = e.target.checked; });
  el.modelSelect.addEventListener('change', e => {
    state.provider = e.target.value;
    if (backend && backend.checkProviderKey) {
      backend.checkProviderKey(state.provider).then(function (hasKey) {
        updateKeyBadge(hasKey);
      });
    }
  });

  // Botão Organizar Acervo / Interromper
  el.btnOrganize.addEventListener('click', () => {
    if (state.isRunning) {
      // Interromper
      if (backend && backend.cancelPipeline) {
        backend.cancelPipeline();
        el.organizeLabel.textContent = 'Finalizando estágio atual...';
        el.btnOrganize.disabled = true;
      }
    } else {
      // Validar pastas
      if (!state.sourceDir) {
        alert('Por favor, selecione a pasta de Origem.');
        return;
      }
      if (!state.targetDir) {
        alert('Por favor, selecione a pasta de Destino.');
        return;
      }

      state.isRunning = true;
      state.items = []; // Limpar lote anterior
      state.selectedPath = null;
      closeCompletionModal();
      if (el.completionBanner) el.completionBanner.style.display = 'none';
      renderTable();
      updateCounters();
      updateOrganizeButton();

      const params = {
        source_dir: state.sourceDir,
        target_dir: state.targetDir,
        provider: state.provider,
        file_operation: state.fileOperation,
        recursive: state.recursive,
        dry_run: state.dryRun,
      };

      if (backend && backend.startOrganize) {
        backend.startOrganize(JSON.stringify(params));
      }
    }
  });

  function updateOrganizeButton() {
    el.btnOrganize.disabled = false;
    if (state.isRunning) {
      el.btnOrganize.className = 'btn btn-danger';
      el.organizeLabel.textContent = 'Interromper Lote';
      el.organizeIcon.innerHTML = '<rect x="6" y="6" width="12" height="12"></rect>';
    } else {
      el.btnOrganize.className = 'btn btn-primary';
      el.organizeLabel.textContent = 'Organizar Acervo';
      el.organizeIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
    }
  }

  // Botões de Rodapé do Inspetor (Priorizando o arquivo e pasta de destino)
  el.btnOpenPdf.addEventListener('click', () => {
    if (!state.selectedPath) return;
    const item = state.items.find(i => i.source_path === state.selectedPath);
    // Prioriza o arquivo organizado de destino; se ainda não materializado, abre a origem
    const targetPath = (item && item.destination_path) ? item.destination_path : state.selectedPath;
    if (backend && backend.openPdf) {
      backend.openPdf(targetPath);
    }
  });

  el.btnRevealFolder.addEventListener('click', () => {
    if (!state.selectedPath) return;
    const item = state.items.find(i => i.source_path === state.selectedPath);
    // Prioriza o local de destino no Finder / Gerenciador de arquivos
    const targetPath = (item && item.destination_path) ? item.destination_path : state.selectedPath;
    if (backend && backend.revealPath) {
      backend.revealPath(targetPath);
    }
  });

  // Preferências e Cache
  el.btnPreferences.addEventListener('click', () => {
    if (backend && backend.openPreferences) backend.openPreferences();
  });
  el.btnCache.addEventListener('click', () => {
    if (backend && backend.openCacheDialog) backend.openCacheDialog();
  });

  // Filtros da Barra Lateral
  el.filterList.querySelectorAll('.filter-item').forEach(item => {
    item.addEventListener('click', () => {
      el.filterList.querySelectorAll('.filter-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      state.activeFilter = item.getAttribute('data-filter');
      renderTable();
    });
  });

  // Busca Instantânea
  el.searchInput.addEventListener('input', e => {
    state.searchQuery = e.target.value;
    el.btnClearSearch.style.display = state.searchQuery ? 'block' : 'none';
    renderTable();
  });

  el.btnClearSearch.addEventListener('click', () => {
    el.searchInput.value = '';
    state.searchQuery = '';
    el.btnClearSearch.style.display = 'none';
    renderTable();
    el.searchInput.focus();
  });

  // --- Limpeza da Tela para Novo Lote ---
  function clearScreenForNewBatch() {
    closeCompletionModal();
    state.items = [];
    state.selectedPath = null;
    state.activeFilter = 'all';
    state.activeAreaFilter = null;
    state.searchQuery = '';
    el.searchInput.value = '';
    if (el.btnClearSearch) el.btnClearSearch.style.display = 'none';
    if (el.completionBanner) el.completionBanner.style.display = 'none';

    // Reset status bar
    el.progressBarFill.style.width = '0%';
    el.progressPct.textContent = '0%';
    el.stageIndicator.textContent = 'Estágio: Ocioso';
    el.countIndicator.textContent = '0 / 0 processados';
    el.remainingIndicator.textContent = 'Restam: 0';
    el.qualityMetric.className = 'quality-metric badge-gray';
    el.qualityMetric.textContent = 'Revisão Manual: 0,0%';

    // Reset filtros na barra lateral
    el.filterList.querySelectorAll('.filter-item').forEach(i => i.classList.remove('active'));
    const allFilterItem = el.filterList.querySelector('[data-filter="all"]');
    if (allFilterItem) allFilterItem.classList.add('active');

    updateCounters();
    updateTaxonomyTree();
    renderTable();
    renderInspector(null);
  }

  if (el.btnClearBatch) {
    el.btnClearBatch.addEventListener('click', (e) => {
      e.stopPropagation();
      clearScreenForNewBatch();
    });
  }
  if (el.completionBanner) {
    el.completionBanner.addEventListener('click', () => {
      clearScreenForNewBatch();
    });
  }

  // --- Eventos do Modal Popup de Conclusão ---
  if (el.btnModalClose) {
    el.btnModalClose.addEventListener('click', closeCompletionModal);
  }
  if (el.btnModalReview) {
    el.btnModalReview.addEventListener('click', () => {
      closeCompletionModal();
      if (state.items.length > 0 && !state.selectedPath) {
        selectItem(state.items[0].source_path);
      }
    });
  }
  if (el.btnModalClear) {
    el.btnModalClear.addEventListener('click', () => {
      closeCompletionModal();
      clearScreenForNewBatch();
    });
  }
  if (el.completionModal) {
    el.completionModal.addEventListener('click', (e) => {
      if (e.target === el.completionModal) {
        closeCompletionModal();
      }
    });
  }
  // --- Eventos do Modal "Sobre o BiblioTEC" ---
  function openAboutModal() {
    if (el.aboutModal) {
      el.aboutModal.style.display = 'flex';
    }
  }

  function closeAboutModal() {
    if (el.aboutModal) {
      el.aboutModal.style.display = 'none';
    }
  }

  if (el.btnAbout) {
    el.btnAbout.addEventListener('click', openAboutModal);
  }
  if (el.btnAboutClose) {
    el.btnAboutClose.addEventListener('click', closeAboutModal);
  }
  if (el.btnAboutOk) {
    el.btnAboutOk.addEventListener('click', closeAboutModal);
  }
  if (el.aboutModal) {
    el.aboutModal.addEventListener('click', (e) => {
      if (e.target === el.aboutModal) {
        closeAboutModal();
      }
    });
  }

  // Copiar chave Pix
  if (el.btnCopyPix && el.pixKeyInput) {
    el.btnCopyPix.addEventListener('click', () => {
      const pix = el.pixKeyInput.value.trim();
      navigator.clipboard.writeText(pix).then(() => {
        const orig = el.btnCopyPix.innerHTML;
        el.btnCopyPix.innerHTML = '✔ Copiado!';
        setTimeout(() => { el.btnCopyPix.innerHTML = orig; }, 1800);
      });
    });
  }

  // Links externos no Modal Sobre
  document.querySelectorAll('.link-external').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const url = link.getAttribute('data-url');
      if (backend && backend.openExternalUrl) {
        backend.openExternalUrl(url);
      } else {
        window.open(url, '_blank');
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (el.aboutModal && el.aboutModal.style.display === 'flex') {
        closeAboutModal();
      } else if (el.completionModal && el.completionModal.style.display === 'flex') {
        closeCompletionModal();
      }
    }
  });

  // --- Utilitários ---
  function getFilename(path) {
    if (!path) return '';
    return path.replace(/^.*[\\/]/, '');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Dados Mock para teste no navegador comum
  function setupMockData() {
    setSource('~/Desktop/origem');
    setTarget('~/Desktop/destino_gui');
    state.items = [
      {
        source_path: '/Users/dario/Desktop/origem/Vygotsky - Pensamento e Linguagem.pdf',
        destination_path: '/Users/dario/Desktop/destino_gui/Ciências Humanas/Psicologia/Livro/VYGOTSKY_2003.pdf',
        status: 'organized',
        title: 'Pensamento e Linguagem',
        authors: ['Vygotsky, Lev Semenovitch'],
        year: 2003,
        grande_area: 'Ciências Humanas',
        area_basica: 'Psicologia',
        tipo: 'Livro',
        confidence: 0.98,
        sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
      },
      {
        source_path: '/Users/dario/Desktop/origem/CamScanner_documento.pdf',
        destination_path: '',
        status: 'manual_review',
        title: 'Documento sem título legível',
        authors: ['Autor Desconhecido'],
        year: null,
        grande_area: 'Ciências Humanas',
        area_basica: 'Sociologia',
        tipo: 'Outros',
        confidence: 0.45,
        reasoning: 'O texto extraído contém apenas a marca d\'água \'Scanned with CamScanner\'.',
        sha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
      }
    ];
    updateCounters();
    updateTaxonomyTree();
    renderTable();
    selectItem(state.items[0].source_path);
  }

  // Inicializar quando o DOM estiver pronto
  document.addEventListener('DOMContentLoaded', initWebChannel);

})();
