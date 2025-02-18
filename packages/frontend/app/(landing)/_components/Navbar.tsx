"use client";

import React from "react";
import { FaGithub } from "react-icons/fa";

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-gradient-to-br from-[#0F172A] to-[#1E3A8A] px-4 py-3 shadow-lg backdrop-blur-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center">
          <h1 className="text-xl font-bold text-white">Wallstr.chat</h1>
        </div>

        <div className="hidden md:flex space-x-6">
          <a href="#features" className="text-white/90 hover:text-blue-300 transition-colors text-sm">
            Features
          </a>
          <a href="#equity-research" className="text-white/90 hover:text-blue-300 transition-colors text-sm">
            How it works
          </a>
        </div>

        <div className="flex items-center space-x-2">
          <div className="hidden md:flex items-center space-x-1">
            <a
              href="https://github.com/limanAI/wallstr"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 bg-gray-800 hover:bg-gray-700 text-white font-semibold px-2 py-1 rounded transition transform hover:scale-105"
            >
              <FaGithub size={14} />
              <span className="text-xs">Github</span>
            </a>
          </div>

          <a href="mailto:team@wallstr.chat?subject=Demo%20Request&body=Hello,%20I%20would%20like%20to%20book%20a%20demo.">
            <button className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-1 shadow-md transition-all transform hover:scale-105 rounded">
              Book a Demo
            </button>
          </a>
        </div>
      </div>
    </nav>
  );
}
