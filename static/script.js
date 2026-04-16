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






}