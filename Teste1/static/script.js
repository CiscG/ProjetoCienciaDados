<<<<<<< HEAD
let chartHist, chartOgiva;
let estatisticasGlobais = null;
let tipoAnaliseAtual = "Notas"; // Controla se estamos vendo Notas ou Anos

// BUSCA COMUM POR NOME
async function buscarDados() {
    const q = document.getElementById("query").value;
    const fonte = document.getElementById("fonte").value;
    if(!q) return alert("Digite algo para pesquisar!");

    tipoAnaliseAtual = "Notas";
    document.getElementById("th-classe").innerText = `Classe (Notas)`;

    const res = await fetch(`/buscar_${fonte}?q=${q}`);
    const itens = await res.json();
    
    if(itens.length < 2) return alert("Poucos dados encontrados para análise.");

    const notas = itens.map(i => i.nota);
    analisar(notas);
}

// NOVA BUSCA TOP 50 (NOTA OU ANO)
async function buscarTop50() {
    const fonte = document.getElementById("fonteTop").value;
    const agruparPor = document.getElementById("agruparPor").value;

    tipoAnaliseAtual = agruparPor === "nota" ? "Notas" : "Anos";
    document.getElementById("th-classe").innerText = `Classe (${tipoAnaliseAtual})`;

    try {
        const res = await fetch(`/buscar_top50?tipo=${fonte}`);
        const itens = await res.json();
        
        if (itens.erro) return alert("Erro na API: " + itens.erro);
        if (itens.length < 2) return alert("Poucos dados encontrados.");

        // Filtra para mandar só as Notas ou só os Anos para o Python
        const valoresParaAnalisar = itens.map(i => i[agruparPor]);
        analisar(valoresParaAnalisar);

    } catch (e) {
        console.error(e);
        alert("Erro ao buscar o Top 50.");
    }
}

// CHAMA O PYTHON PARA CALCULAR A ESTATÍSTICA
async function analisar(dados) {
    const res = await fetch("/analisar", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({dados})
    });
    const r = await res.json();
    estatisticasGlobais = r;

    renderTabela(r);
    renderMedidas(r);
    renderGraficos(r);
}

// RENDERIZAÇÕES
function renderTabela(r) {
    const tbody = document.getElementById("tabela-body");
    tbody.innerHTML = r.classes.map((c, i) => `
        <tr>
            <td>${c[0]} |- ${c[1]}</td>
            <td>${r.fi[i]}</td>
            <td>${r.fa[i]}</td>
            <td>${r.xi[i].toFixed(2)}</td>
        </tr>
    `).join("");
}

function renderMedidas(r) {
    const div = document.getElementById("medidas-stats");
    div.innerHTML = `
        <div class="stat-item"><b>Média:</b> ${r.media}</div>
        <div class="stat-item"><b>Desvio Padrão:</b> ${r.dp}</div>
        <div class="stat-item"><b>Variância:</b> ${r.variancia}</div>
        <div class="stat-item"><b>Coef. Variação:</b> ${r.cv.toFixed(2)}%</div>
        <div class="stat-item"><b>Tamanho (n):</b> ${r.n}</div>
        <div class="stat-item"><b>Amplitude:</b> ${r.max - r.min}</div>
    `;
}

function renderGraficos(r) {
    const labels = r.classes.map(c => `${c[0]} |- ${c[1]}`);
    
    if(chartHist) chartHist.destroy();
    chartHist = new Chart(document.getElementById("histChart"), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{ label: 'Frequência Absoluta (fi)', data: r.fi, backgroundColor: '#3b82f6' }]
        }
    });

    if(chartOgiva) chartOgiva.destroy();
    chartOgiva = new Chart(document.getElementById("ogivaChart"), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{ label: 'Frequência Acumulada (fa)', data: r.fa, borderColor: '#ef4444', fill: false }]
        }
    });
}

// EXPORTAÇÕES
function exportarCSV() {
    if(!estatisticasGlobais) return;
    let csv = `Classe_Inicio,Classe_Fim,fi,fa,xi\n`;
    estatisticasGlobais.classes.forEach((c, i) => {
        csv += `${c[0]},${c[1]},${estatisticasGlobais.fi[i]},${estatisticasGlobais.fa[i]},${estatisticasGlobais.xi[i]}\n`;
    });
    const blob = new Blob([csv], {type: 'text/csv'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `estatistica_${tipoAnaliseAtual}.csv`; a.click();
}

function exportarPDF() {
    if(!estatisticasGlobais) return;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    doc.text(`Relatório de Estatística Descritiva - Analisando ${tipoAnaliseAtual}`, 10, 10);
    doc.text(`Amostra (n): ${estatisticasGlobais.n} | Média: ${estatisticasGlobais.media}`, 10, 20);
    
    doc.autoTable({
        startY: 30,
        head: [[`Classe (${tipoAnaliseAtual})`, 'fi', 'fa', 'xi']],
        body: estatisticasGlobais.classes.map((c, i) => [
            `${c[0]} |- ${c[1]}`, estatisticasGlobais.fi[i], estatisticasGlobais.fa[i], estatisticasGlobais.xi[i]
        ])
    });
    doc.save(`relatorio_${tipoAnaliseAtual}.pdf`);
=======
let chartH;
let chartO; // Variável global para controlar o gráfico da Ogiva

async function buscarTop50() {
    const btn = document.querySelector(".btn-purple");
    const fonte = document.getElementById("fonteTop").value;
    const campo = document.getElementById("agruparPor").value;
    
    btn.innerText = "⏳ Processando...";
    
    try {
        const res = await fetch(`/buscar_top50?tipo=${fonte}&campo=${campo}`);
        const itens = await res.json();
        
        const resAnalise = await fetch("/analisar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({dados: itens})
        });
        const r = await resAnalise.json();
        renderUI(r);
    } catch (err) {
        alert("Erro de conexão com o servidor Flask.");
    } finally {
        btn.innerText = "⚡ Extrair e Analisar";
    }
}

function renderUI(r) {
    // Tabela de Classes
    document.getElementById("tabela-body").innerHTML = r.classes.map((c, i) => 
        `<tr><td>${c[0]} |- ${c[1]}</td><td>${r.fi[i]}</td><td>${r.fa[i]}</td><td>${r.xi[i]}</td></tr>`
    ).join("");

    // Quadro de Medidas de Resumo
    document.getElementById("medidas-stats").innerHTML = `
        <div class="stat-item"><b>Média:</b> ${r.media}</div>
        <div class="stat-item"><b>Desvio Padrão:</b> ${r.dp}</div>
        <div class="stat-item"><b>Variância:</b> ${r.variancia}</div>
        <div class="stat-item"><b>Coef. Variação:</b> ${r.cv}%</div>
        <div class="stat-item"><b>Mediana:</b> ${r.mediana}</div>
        <div class="stat-item"><b>Moda:</b> ${r.moda}</div>
        <div class="stat-item"><b>Tamanho (n):</b> ${r.n}</div>
        <div class="stat-item"><b>Amplitude:</b> ${r.at}</div>
    `;

    // Lista de Auditoria
    const tbodyAuditoria = document.querySelector("#tabela-auditoria tbody");
    tbodyAuditoria.innerHTML = r.itens_completos.map(item => 
        `<tr><td>${item.titulo}</td><td>${item.nota}</td><td>${item.ano}</td></tr>`
    ).join("");

    // Histograma
    const ctx = document.getElementById("histChart").getContext("2d");
    if(chartH) chartH.destroy();
    chartH = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: r.classes.map(c => `${c[0]}-${c[1]}`),
            datasets: [{
                label: 'Frequência (fi)',
                data: r.fi,
                backgroundColor: '#8b5cf6'
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Lógica para renderizar a Ogiva de Galton
const ctxO = document.getElementById("ogivaChart").getContext("2d");

// Destrói o gráfico anterior se ele já existir para evitar sobreposição
if (chartO) chartO.destroy();

chartO = new Chart(ctxO, {
    type: 'line',
    data: {
        // Usa os intervalos das classes como labels no eixo X
        labels: r.classes.map(c => `${c[0]} |- ${c[1]}`),
        datasets: [{
            label: 'Frequência Acumulada (fa)',
            data: r.fa, // Dados da frequência acumulada vindos do backend
            borderColor: '#ef4444', // Cor vermelha conforme a imagem
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.1, // Linhas retas ou levemente curvas entre os pontos
            pointRadius: 5,
            pointBackgroundColor: '#ef4444'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                max: 50, // Limite máximo de n=50
                title: { display: true, text: 'Frequência Acumulada' }
            }
        }
    }
    });






>>>>>>> ed3036d (terminando essa merda)
}