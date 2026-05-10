// src/components/TagInput.jsx

import React, { useState, useRef, useEffect } from "react";
import { X, Plus, ChevronDown } from "lucide-react";

export default function TagInput({
  value = [],
  onChange,
  suggestions = [],
  placeholder = "Add tags...",
  maxTags = 20,
  className = "",
}) {
  const [inputValue, setInputValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  const tags = Array.isArray(value) ? value : value.split(",").map(t => t.trim()).filter(t => t);

  const filteredSuggestions = suggestions.filter(
    s => !tags.includes(s) && s.toLowerCase().includes(inputValue.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const addTag = (tag) => {
    const trimmedTag = tag.trim();
    if (!trimmedTag) return;
    if (tags.length >= maxTags) return;
    if (tags.includes(trimmedTag)) return;

    const newTags = [...tags, trimmedTag];
    onChange(newTags);
    setInputValue("");
    setShowSuggestions(false);
    setSelectedIndex(-1);
  };

  const removeTag = (indexToRemove) => {
    const newTags = tags.filter((_, index) => index !== indexToRemove);
    onChange(newTags);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      if (selectedIndex >= 0 && filteredSuggestions[selectedIndex]) {
        addTag(filteredSuggestions[selectedIndex]);
      } else if (inputValue.trim()) {
        addTag(inputValue);
      }
    } else if (e.key === "Backspace" && !inputValue && tags.length > 0) {
      removeTag(tags.length - 1);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(prev => 
        prev < filteredSuggestions.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    addTag(suggestion);
    inputRef.current?.focus();
  };

  const getTagColor = (tag) => {
    const colors = [
      "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
      "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
      "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
      "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
      "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400",
      "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
    ];
    const index = tag.length % colors.length;
    return colors[index];
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="flex flex-wrap gap-2 p-2 min-h-[42px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus-within:ring-2 focus-within:ring-blue-500">
        {tags.map((tag, index) => (
          <span
            key={index}
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getTagColor(tag)}`}
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="hover:bg-black/10 rounded-full p-0.5"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setShowSuggestions(true);
            setSelectedIndex(-1);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowSuggestions(true)}
          placeholder={tags.length === 0 ? placeholder : ""}
          disabled={tags.length >= maxTags}
          className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-gray-900 dark:text-white placeholder-gray-400 disabled:opacity-50"
        />
        
        {filteredSuggestions.length > 0 && (
          <button
            type="button"
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${showSuggestions ? "rotate-180" : ""}`} />
          </button>
        )}
      </div>

      {tags.length >= maxTags && (
        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
          Maximum {maxTags} tags reached
        </p>
      )}

      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => handleSuggestionClick(suggestion)}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 ${
                index === selectedIndex ? "bg-blue-50 dark:bg-blue-900/30" : ""
              }`}
            >
              <Plus className="w-3 h-3 text-gray-400" />
              <span className="text-gray-700 dark:text-gray-300">{suggestion}</span>
            </button>
          ))}
        </div>
      )}

      {showSuggestions && inputValue && filteredSuggestions.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <button
            type="button"
            onClick={() => addTag(inputValue)}
            className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-blue-600 dark:text-blue-400"
          >
            <Plus className="w-3 h-3" />
            Add "{inputValue}"
          </button>
        </div>
      )}
    </div>
  );
}