# Competitive Programming Assistant - MCP Server

![Python](https://img.shields.io/badge/language-Python-blue?style=flat-square)

A comprehensive Model Context Protocol (MCP) server designed to enhance competitive programming workflows through intelligent data analysis, visualization, and problem recommendations. Built for the hackathon, this project integrates with Codeforces API to provide actionable insights for competitive programmers.

## Overview

This MCP server provides a suite of tools specifically designed for competitive programming enthusiasts, coaches, and students. It offers real-time statistics, intelligent problem recommendations, performance analytics, and comprehensive visualizations to help users improve their competitive programming skills systematically.

## Core Functionality

### User Statistics and Analytics
- **User Profile Analysis**: Fetch detailed statistics for single or multiple Codeforces users
- **Rating History Tracking**: Monitor rating changes and contest performance over time
- **Performance Metrics**: Calculate true performance ratings using advanced algorithms
- **Activity Monitoring**: Track recent problem-solving activity and submission patterns

### Problem Recommendation System
- **Intelligent Recommendations**: AI-powered problem suggestions based on user rating and solving history
- **Difficulty Targeting**: Customizable rating ranges for personalized practice sessions
- **Unsolved Problem Detection**: Ensures recommendations are fresh and challenging
- **Practice Optimization**: Helps users focus on problems that will maximize improvement

### Data Visualization Tools
- **Rating Graphs**: Multi-user rating comparison with timestamp analysis
- **Performance Charts**: Contest-by-contest performance visualization with rank-based color coding
- **Distribution Analysis**: Rating distribution histograms showing solving patterns
- **Verdict Analytics**: Success rate analysis across different problem types
- **Topic Proficiency**: Tag-based problem distribution visualization
- **Language Usage**: Programming language preference analysis

### Contest Analysis
- **Rating Change Tracking**: Detailed contest performance with rank and rating delta analysis
- **Historical Performance**: Long-term trend analysis for strategic improvement
- **Upsolve Identification**: Find contests with optimal completion potential

## Available Tools

### Core Statistics Tools
- `get_codeforces_user_stats` - Comprehensive user profile and rating information
- `get_solved_problems` - Recent solving activity with timestamps and ratings
- `get_rating_changes` - Contest performance history with detailed metrics
- `get_solved_rating_histogram` - Text-based rating distribution analysis

### Recommendation Engine
- `recommend_problems` - Intelligent problem suggestions based on user profile
- `get_upsolve_targets` - Contest completion optimization recommendations

### Visualization Suite
- `plot_rating_graph` - Multi-user rating progression visualization
- `plot_performance_graph` - True performance rating with rank-based backgrounds
- `plot_solved_rating_distribution` - Visual histogram of solved problem ratings
- `plot_verdict_distribution` - Success rate analysis across submission verdicts
- `plot_tag_distribution` - Topic-wise problem solving proficiency
- `plot_language_distribution` - Programming language usage patterns

### External Integrations
- `get_upcoming_contests` - Multi-platform contest schedule aggregation
- `get_leetcode_daily_problem` - Daily challenge integration for diverse practice

## Technical Architecture

### API Integration
- **Codeforces API**: Primary data source for user statistics, problems, and contest information
- **Clist API**: Contest aggregation from multiple competitive programming platforms
- **LeetCode Integration**: Daily problem fetching for supplementary practice

### Data Processing
- **Concurrent API Calls**: Optimized performance using asyncio for parallel data fetching
- **Intelligent Caching**: Reduces API load and improves response times
- **Error Handling**: Robust error management with meaningful user feedback

### Visualization Engine
- **Matplotlib Integration**: High-quality chart generation with customizable styling
- **Base64 Encoding**: Efficient image delivery through MCP protocol
- **Responsive Design**: Charts optimized for various display contexts

### Health Monitoring
- **Keep-Alive System**: Automatic health checks to maintain server availability
- **Performance Monitoring**: Built-in health endpoints for deployment monitoring
- **Configurable Intervals**: Customizable ping frequency for different environments






### Production Deployment
```
Optimized for Render deployment with automatic keep-alive functionality. The health monitoring system ensures continuous availability on free-tier hosting platforms.

```

## Project Structure
```
competitive-programming-assistant/
├── api_clients/           # External API integration modules
├── tools/                 # MCP tool implementations
│   ├── codeforces_tools.py   # Core statistics and recommendations
│   └── graphing_tools.py     # Visualization tools
├── config.py             # Configuration management
├── server.py             # MCP server implementation
└── requirements.txt      # Python dependencies
```

## Hackathon Context

This project was developed as a comprehensive solution for competitive programming education and improvement. It addresses real challenges faced by competitive programmers:

- **Data Accessibility**: Transforms raw API data into actionable insights
- **Learning Optimization**: Provides data-driven practice recommendations
- **Progress Tracking**: Offers comprehensive performance visualization
- **Multi-Platform Integration**: Aggregates data from various competitive programming platforms

The MCP protocol integration enables seamless integration with AI assistants, making competitive programming guidance more accessible and intelligent.

## Use Cases

### Individual Practice
- Track personal progress and identify improvement areas
- Receive targeted problem recommendations based on current skill level
- Visualize performance trends across different contest types

### Coaching and Education
- Compare multiple students' progress simultaneously
- Identify common weak areas across a group
- Generate data-driven practice plans for systematic improvement

### Contest Preparation
- Analyze historical performance patterns
- Identify optimal practice problems for rating improvement
- Track consistency and solving speed metrics

## Future Enhancements

- Machine learning-based difficulty prediction
- Cross-platform performance correlation analysis
- Advanced coaching dashboard features
- Real-time contest monitoring and alerts

This project demonstrates the power of combining competitive programming domain expertise with modern API integration and data visualization techniques, creating a comprehensive tool for the competitive programming
