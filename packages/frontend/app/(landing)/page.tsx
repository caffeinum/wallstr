"use client";
import { AgGridReact } from "ag-grid-react";
import { ClientSideRowModelModule, ColDef } from "ag-grid-community";
import { useRouter } from "next/navigation";

import Navbar from "./_components/Navbar";
import Footer from "./_components/Footer";

import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import "./style.css";

const FeatureIcons = {
  analysis: (
    <svg className="w-12 h-12 mb-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      />
    </svg>
  ),
  memos: (
    <svg className="w-12 h-12 mb-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  ),
  security: (
    <svg className="w-12 h-12 mb-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
      />
    </svg>
  ),
};

type TExampleQuery = {
  step: string;
  question: string;
  insight: string;
  source: string;
};

const examples = [
  {
    step: "📊 Business Model",
    question: "What is Company X’s core revenue driver, and how has it evolved?",
    insight:
      "Company X generates 75% of revenue from recurring SaaS contracts, transitioning from a licensing model over five years. LTV increased from $18K to $24K per client, while gross margins expanded from 52% to 58%.",
    source: "10-K, Earnings Calls, Investor Presentations",
  },
  {
    step: "💰 Financial Performance",
    question: "How does inflation impact Company X’s cost structure?",
    insight:
      "Input costs increased 7% YoY, driven by rising supply chain expenses and labor costs. However, Company X offset inflation through price adjustments and efficiency gains, maintaining an operating margin of 24.5%, compared to 23.8% a year prior.",
    source: "SEC Filings, Analyst Coverage Reports",
  },
  {
    step: "🏆 Competitive Positioning",
    question: "How does Company X defend market share from new entrants?",
    insight:
      "Company X maintains a 32% market share, leveraging strong network effects and switching costs. Over 60% of customers integrate Company X’s platform across multiple business units, making replacement costly and inefficient.",
    source: "Competitor 10-Ks, Market Research, Earnings Call Q&A",
  },
  {
    step: "🌎 Market Expansion",
    question: "What is the upside potential of Company X’s international expansion?",
    insight:
      "Company X is expanding into [New Market], a $12B opportunity growing at 14% CAGR. Regulatory approvals were recently secured, and initial pilot projects indicate a 20%+ market penetration rate within five years.",
    source: "Investor Presentations, Earnings Calls, Market Research Reports",
  },
  {
    step: "⚠ Risk Factors",
    question: "What regulatory risks could impact Company X’s operations?",
    insight:
      "New data privacy laws in [Region] could increase compliance costs by $50M annually, impacting EBITDA margins by 0.6 percentage points. However, Company X has already begun adapting its data architecture to mitigate long-term risk.",
    source: "10-K (Risk Section), Legal Filings, Regulatory Disclosures",
  },
];

const columnDefs: ColDef<TExampleQuery>[] = [
  {
    headerName: "Section",
    field: "step",
    width: 220,
    cellStyle: {
      fontWeight: "bold",
      fontSize: "",
      color: "#E5C100",
      display: "flex",
      alignItems: "center",
    },
  },
  {
    headerName: "Question",
    field: "question",
    flex: 1.8,
    wrapText: true,
    autoHeight: true,
    cellStyle: {
      fontSize: "10px",
      fontWeight: "600",
      color: "#EAEAEA",
    },
  },
  {
    headerName: "Answer",
    field: "insight",
    flex: 2.2,
    wrapText: true,
    autoHeight: true,
    cellStyle: {
      fontSize: "10px",
      lineHeight: "1.6",
      whiteSpace: "pre-wrap",
      color: "#D0D0D0",
    },
  },
  {
    headerName: "Sources",
    field: "source",
    flex: 1,
    wrapText: true,
    autoHeight: true,
    cellStyle: {
      fontSize: "12px",
      color: "#60A5FA",
      cursor: "pointer",
      textDecoration: "underline",
      fontWeight: "600",
    },
  },
];

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="bg-base-100 min-h-screen font-sans text-base-content">
      <Navbar />

      <section
        id="hero"
        className="relative bg-gradient-to-br from-[#0F172A] to-[#1E3A8A] py-40 px-4 text-center text-white"
      >
        <div className="max-w-6xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 drop-shadow-lg">
            Transform Hours of Research into Minutes
          </h1>
          <p className="text-xl text-white/80 max-w-3xl mx-auto mb-12">
            Institutional-grade AI analysis trusted by Street investment bankers
          </p>
          <button
            onClick={() => router.push("/chat")}
            className="btn bg-blue-600 hover:bg-blue-500 text-white text-lg px-10 py-4 rounded-lg font-semibold shadow-lg transition-transform transform hover:scale-105"
          >
            Join Professionals Saving 15+ Hours Weekly →
          </button>
        </div>
      </section>

      <section id="features" className="py-24 px-4 text-center">
        <h2 className="text-4xl font-bold mb-12">Why Choose Wallstr.chat?</h2>
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12">
          {[
            {
              title: "AI-Powered Document Analysis",
              icon: FeatureIcons.analysis,
              description: "Secure AI-driven insights with local data storage.",
            },
            {
              title: "Professional Investment Guidance",
              icon: FeatureIcons.memos,
              description: "Every response is sourced and data-backed.",
            },
            {
              title: "Clear & Structured Insights",
              icon: FeatureIcons.security,
              description: "Precision and transparency in every answer.",
            },
          ].map((feature, index) => (
            <div key={index} className="card bg-base-200 p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
              <div className="flex justify-center mb-4">{feature.icon}</div>
              <h3 className="text-2xl font-semibold mb-4">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="equity-research" className="py-16 px-4 bg-[#0B0F19]">
        <div className="max-w-7xl mx-auto bg-[#10131A] p-8 rounded-2xl border border-[#2E323F] shadow-2xl">
          <h2 className="text-4xl font-bold text-center text-white mb-6">AI-Powered Equity Research</h2>
          <p className="text-center text-lg text-gray-400 mb-8">
            Unlike generic AI models, our system builds a custom knowledge base for each company, ensuring deep,
            verifiable insights tailored to your research.
          </p>

          <div
            className="rounded-lg shadow-lg overflow-hidden border border-[#2E323F] bg-[#0A0F1D]"
            style={{ height: 500, width: "100%" }}
          >
            <AgGridReact
              rowData={examples}
              columnDefs={columnDefs}
              modules={[ClientSideRowModelModule]}
              pagination={true}
              paginationPageSize={5}
              rowHeight={100}
              suppressRowHoverHighlight={false}
              gridOptions={{
                headerHeight: 50,
                theme: "legacy",
              }}
              defaultColDef={{
                resizable: true,
                sortable: true,
                filter: true,
                wrapText: true,
                autoHeight: false,
                flex: 1,
                cellStyle: (params) => ({
                  whiteSpace: "normal",
                  fontSize: "13px",
                  lineHeight: "1.3",
                  padding: "10px",
                  color: "#E5E7EB",
                  backgroundColor: (params.node.rowIndex ?? 0) % 2 === 0 ? "#151A28" : "#1A1F2F",
                }),
              }}
            />
          </div>
        </div>
      </section>

      <section id="cta" className="py-24 bg-[#0F172A] text-center text-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold mb-6">Start Your AI-Powered Research Today</h2>
          <p className="text-lg mb-8">Join Street&apos;s funds accelerating their due diligence with Wallstr.chat</p>
          <div className="flex flex-col md:flex-row gap-4 justify-center">
            <button
              className="btn bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 text-lg font-semibold"
              onClick={() => router.push("/chat")}
            >
              Get Instant Access
            </button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
