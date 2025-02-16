# Influencer Engagement and Sponsorship Coordination Platform (IESCP)

## Deployment Link
[IESCP Live](https://iescp.pythonanywhere.com)

## Project Overview
**Influencer Engagement and Sponsorship Coordination Platform (IESCP)** is a web-based platform designed to connect **Sponsors** and **Influencers** for seamless collaboration. Sponsors can advertise their products/services through influencers, while influencers can benefit monetarily by engaging in promotional campaigns.

## Tech Stack
- **Backend:** Flask
- **Frontend:** Jinja2 Templates, Bootstrap
- **Database:** SQLite

## Core Features
### 1. **User Roles**
- **Admin:**
  - Monitor all users and campaigns
  - View platform statistics
  - Flag inappropriate campaigns/users
- **Sponsors:**
  - Create and manage campaigns
  - Search for influencers
  - Send and track ad requests
  - Accept influencer ad requests for public campaigns
- **Influencers:**
  - Receive, accept, reject, and negotiate ad requests
  - Search for public campaigns
  - Maintain a publicly visible profile

### 2. **Ad Requests**
- Acts as a contract between **campaigns** and **influencers**
- Includes requirements, payment amount, and status tracking

### 3. **Campaign Management**
- Sponsors can create, update, and delete campaigns
- Campaigns can be categorized and set as public or private

### 4. **Search Functionality**
- Sponsors can search influencers based on niche, reach, and followers
- Influencers can search public campaigns by category and budget

### 5. **Admin Dashboard**
- Displays active users, campaigns, ad requests, and flagged accounts

## Recommended Features
- API resources for users, campaigns, and ad requests
- ChartJS integration for analytics
- Frontend validation using HTML5 and JavaScript
- Backend validation in Flask controllers

## Optional Enhancements
- Improved UI with Bootstrap styling
- Flask login system for secure access control
- Dummy payment gateway for ad requests

## Database Schema (ER Diagram)
The project follows a relational model with tables for **Users (Admin, Sponsors, Influencers), Campaigns, and Ad Requests**.

## Evaluation Criteria
- Functional implementation of core features
- Project report (including database schema, API endpoints, and a presentation video link)
- Live demonstration and viva

## Submission Guidelines
- The project should be submitted as a **single zip file**.
- Include a **project report (PDF format)** within the submission folder.
- A **brief video (3–5 minutes)** explaining the implementation must be uploaded with an accessible link in the report.

For detailed requirements, refer to the [official project document](https://docs.google.com/document/d/e/2PACX-1vSWc_RrSIlJZamInJ6n-KZtJkcgTpp-CsaR_-Kq_U5ZwzCf-zWU8b6RmaV86KaNiJVUJ5cFadTr88VI/pub).
