# 👋 Hi, I'm Iliya Haddad

### Systems & Software Engineer · Low-Level · Networking · Infrastructure

> **Don't just use technology. Understand how it works.**

I build and investigate software across different layers of the stack — from **microcontrollers, firmware and legacy hardware** to **Windows drivers, networking, security and modern enterprise applications**.

I enjoy projects where software meets the underlying system.

```text
┌─────────────────────────────────────────────────────────────┐
│                        ILIYA HADDAD                         │
│                                                             │
│   SOFTWARE  ─────── SYSTEMS ─────── HARDWARE               │
│       │                  │                 │                │
│     .NET              Windows            PIC / AVR           │
│     Python            WDDM               USB / IR            │
│     Django            Linux              UART                │
│     React             ConPTY             Legacy              │
│                                                             │
│   NETWORKING ─────── SECURITY ─────── INFRASTRUCTURE        │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Engineering Focus

<table>
<tr>
<td width="33%" valign="top">

### 🖥️ Systems

- Windows internals
- WDDM
- GPU architecture
- Kernel-mode development
- ConPTY
- Legacy software
- DOS / retro computing
- Software reconstruction

</td>

<td width="33%" valign="top">

### 🔌 Embedded

- PIC / AVR
- Assembly
- UART
- USB
- Infrared
- Firmware
- Serial protocols
- Hardware interfaces

</td>

<td width="33%" valign="top">

### 🌐 Networking

- MikroTik RouterOS
- Firewall
- IPS
- Asterisk / Issabel
- VoIP
- VPN
- Linux networking
- Infrastructure

</td>
</tr>
</table>

---

# ⭐ Featured Engineering Projects

These are the projects that best represent how I approach engineering problems.

---

## 🧠 WDDM 2.0 Driver Research

**Legacy AMD Radeon · Windows Kernel · GPU Architecture**

Research and experimental implementation exploring the feasibility of a WDDM 2.0 display driver for legacy AMD Radeon hardware.

### Focus

```text
AMD Evergreen / Madison
        │
        ├── GPU Memory
        ├── Command Submission
        ├── Rings
        ├── Fences
        ├── Interrupts
        ├── Firmware
        └── WDDM Architecture
```

> Research / experimental project — not a production driver.

🔗 **[Explore the project →](https://github.com/iliyahaddad/WDDM-2.0-Driver-For-ATI-AMD-Series-Radeon-HD5000)**

---

## 🔌 UIR Dual-Mode COM / USB

**Embedded Systems · ATtiny85 · USB · Serial · Infrared**

A dual-mode infrared receiver designed around legacy PC serial communication and USB.

```text
                 ┌─────────────┐
Legacy COM ─────►│             │
                 │   ATtiny85  │────► IR
USB / V-USB ───►│             │
                 └─────────────┘
```

### Technologies

`ATtiny85` · `V-USB` · `UART` · `IR` · `Firmware` · `Hardware`

🔗 **[Explore the project →](https://github.com/iliyahaddad/UIR-Dual-Mode-COM-USB)**

---

## 🟢 Matrix Terminal

**Windows · .NET 8 · WPF · ConPTY · VT/ANSI**

A Windows terminal combining a Matrix-inspired interface with a real ConPTY backend.

### Features

- CMD / PowerShell
- VT / ANSI terminal sequences
- 16 / 256 / TrueColor
- Cursor addressing
- Alternate screen
- Scrollback
- Resize handling
- Copy / Paste
- MikroTik-inspired visual theme

> The MikroTik theme is visual; it does not emulate RouterOS.

🔗 **[Explore the project →](https://github.com/iliyahaddad/Matrix-Terminal)**

---

## 🛡️ RouterOS 7 IPS

**MikroTik · Firewall · Network Security**

A lightweight defensive security framework for RouterOS 7.

```text
Traffic
   │
   ▼
┌───────────────┐
│ RAW Firewall  │
├───────────────┤
│ Threat Logic  │
├───────────────┤
│ Address Lists │
├───────────────┤
│ IPv4 / IPv6   │
└───────┬───────┘
        ▼
    Protected
     Network
```

Includes:

- Threat levels
- IPv4 / IPv6 protection
- SYN flood mitigation
- DDoS-oriented rules
- Dynamic address lists
- Security profiles

> Designed as a lightweight RouterOS defensive layer, not a replacement for deep packet inspection systems.

🔗 **[Explore the project →](https://github.com/iliyahaddad/RouterOS7_IPS)**

---

# 🏗️ Enterprise Software

## Technical Inspection Management Platform

A full-stack platform for technical inspection workflows.

**Backend**

`Django` · `Django REST Framework` · `PostgreSQL` · `Redis` · `Celery`

**Frontend**

`React` · `TypeScript` · `Vite`

**Infrastructure**

`Docker` · `Nginx`

🔗 **[Explore the project →](https://github.com/iliyahaddad/Technical-Inspection-Management-Platform)**

---

## 💰 Project Financial Management System

A project-control and financial-management platform covering:

- WBS
- Cost control
- Man-day management
- EAC
- Profitability
- Payment certificates
- RBAC
- Audit logging
- Excel / PDF / CSV reporting
- Persian / RTL workflows

🔗 **[Explore the project →](https://github.com/iliyahaddad/Project-Financial-Management-System)**

---

# 🧪 Research & Legacy Engineering

I have a particular interest in understanding and preserving older technologies.

### 🕹️ Creative QuickCD

Reverse engineering and reconstruction of legacy Creative software.

**Focus:** DOS · Windows · Binary Analysis · Legacy Software

🔗 [Repository](https://github.com/iliyahaddad/Creative-QuickCD)

---

### 💾 Windows 95 Style Exit for DOS

A retro-computing experiment recreating a Windows 95-style exit interface inside a DOS/QBASIC environment while preserving the application's screen and state.

🔗 [Repository](https://github.com/iliyahaddad/Windows-95-Style-Exit-DOS-App)

---

### ☎️ Issabel CCBS

Call Completion on Busy Subscriber for Issabel/Asterisk environments.

**Focus:** Asterisk · Issabel · SIP · VoIP

🔗 [Repository](https://github.com/iliyahaddad/Issabel-CCBS)

---

# 🧰 Other Projects

| Project | Technology / Domain |
|---|---|
| 💊 [Pill Reminder](https://github.com/iliyahaddad/Pill-Reminder) | Kotlin · Android · Jetpack Compose |
| 🏢 [UK Company House Filing](https://github.com/iliyahaddad/UK-Company-House-Filing) | Python · FastAPI · iXBRL |
| 💳 [WordPress Card Transfer Gateway](https://github.com/iliyahaddad/Wordpress-Card-Transfer-Gateway) | PHP · WordPress · WooCommerce |
| 🤖 [VirtualBot](https://github.com/iliyahaddad/VirtualBot) | JavaScript · Discord |
| 🔐 [VPN-UI](https://github.com/iliyahaddad/VPN-UI) | VPN · Linux · Xray / 3X-UI |

---

# 🧱 Technology Stack

### Languages

![C](https://img.shields.io/badge/C-00599C?style=flat-square&logo=c&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-00599C?style=flat-square&logo=c%2B%2B&logoColor=white)
![C#](https://img.shields.io/badge/C%23-512BD4?style=flat-square&logo=csharp&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![PHP](https://img.shields.io/badge/PHP-777BB4?style=flat-square&logo=php&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white)
![Assembly](https://img.shields.io/badge/Assembly-525252?style=flat-square)

### Frameworks

![.NET](https://img.shields.io/badge/.NET-512BD4?style=flat-square&logo=dotnet&logoColor=white)
![ASP.NET Core](https://img.shields.io/badge/ASP.NET_Core-512BD4?style=flat-square&logo=dotnet&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Laravel](https://img.shields.io/badge/Laravel-FF2D20?style=flat-square&logo=laravel&logoColor=white)
![Android](https://img.shields.io/badge/Android-3DDC84?style=flat-square&logo=android&logoColor=white)

### Systems & Infrastructure

![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![MikroTik](https://img.shields.io/badge/MikroTik-293239?style=flat-square)

---

# 🧠 Engineering Philosophy

I like understanding what happens underneath the abstraction.

```text
Application
     │
     ▼
Framework
     │
     ▼
Operating System
     │
     ▼
Driver / Protocol
     │
     ▼
Hardware
```

And on the network side:

```text
Application
     │
     ▼
Protocol
     │
     ▼
Firewall
     │
     ▼
Network Stack
     │
     ▼
Infrastructure
```

The interesting problems are usually somewhere between these layers.

---

# 🔭 Currently Exploring

- Windows Driver Development
- WDDM architecture
- Legacy AMD GPU hardware
- Embedded firmware
- PIC / AVR
- USB and serial protocols
- Network security
- MikroTik RouterOS
- Local AI systems
- Windows terminal technologies
- Legacy software preservation

---

# 📊 GitHub

<p align="center">
  <a href="https://github.com/iliyahaddad">
    <img src="https://github-readme-stats.vercel.app/api?username=iliyahaddad&show_icons=true&hide_border=true&rank_icon=github" height="170">
  </a>
  <a href="https://github.com/iliyahaddad">
    <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=iliyahaddad&layout=compact&hide_border=true" height="170">
  </a>
</p>

---

# 📫 Find Me

**GitHub:** [github.com/iliyahaddad](https://github.com/iliyahaddad)

---

<p align="center">

### Building software. Understanding systems. Connecting the old with the new.

</p>
