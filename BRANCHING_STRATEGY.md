# RTB2000 Git Branching Strategy

## 🌳 Branch Structure

### **Main Branches**

#### 🏠 **main**
- **Purpose:** Production-ready code
- **Protection:** Protected branch, requires PR review
- **Deployment:** Automatically deployed to production
- **Merge policy:** Only from `development` via PR

#### 🔧 **development**
- **Purpose:** Integration branch for features
- **Stability:** Stable, tested features
- **Source:** Feature branches merge here first
- **Testing:** Full test suite runs on every commit

### **Supporting Branches**

#### 🚀 **feature/***
- **Naming:** `feature/description-of-feature`
- **Purpose:** New feature development
- **Lifecycle:** Branch from `development`, merge back to `development`
- **Examples:**
  - `feature/phase3-preparation`
  - `feature/ui-enhancements`
  - `feature/network-connectivity`
  - `feature/cloud-integration`

#### 🐛 **bugfix/***
- **Naming:** `bugfix/description-of-fix`
- **Purpose:** Bug fixes for development branch
- **Lifecycle:** Branch from `development`, merge back to `development`

#### 🚨 **hotfix/***
- **Naming:** `hotfix/critical-fix-description`
- **Purpose:** Critical production fixes
- **Lifecycle:** Branch from `main`, merge to both `main` and `development`

#### 🧪 **experimental/***
- **Naming:** `experimental/research-topic`
- **Purpose:** Research and experimental features
- **Lifecycle:** May be abandoned or converted to feature branch

## 📋 Current Branches

| Branch | Purpose | Status | Last Updated |
|--------|---------|--------|--------------|
| `main` | Production code | ✅ Stable | Sep 8, 2025 |
| `development` | Active development | 🔄 Active | Sep 8, 2025 |
| `feature/phase3-preparation` | Phase 3 planning | 🆕 New | Sep 8, 2025 |
| `feature/ui-enhancements` | UI improvements | 🆕 New | Sep 8, 2025 |

## 🔄 Workflow Process

### **Feature Development**
```bash
# 1. Start new feature
git checkout development
git pull origin development
git checkout -b feature/new-awesome-feature

# 2. Develop and commit
git add .
git commit -m "✨ Add awesome new feature"
git push -u origin feature/new-awesome-feature

# 3. Create Pull Request to development
# 4. After review and approval, merge to development
# 5. Delete feature branch
git branch -d feature/new-awesome-feature
git push origin --delete feature/new-awesome-feature
```

### **Release Process**
```bash
# 1. Create release branch from development
git checkout development
git checkout -b release/v2.6.0

# 2. Final testing and bug fixes
git commit -m "🐛 Fix release bugs"

# 3. Merge to main
git checkout main
git merge release/v2.6.0
git tag -a v2.6.0 -m "Release version 2.6.0"

# 4. Merge back to development
git checkout development
git merge release/v2.6.0

# 5. Push everything
git push origin main
git push origin development
git push origin v2.6.0
```

### **Hotfix Process**
```bash
# 1. Create hotfix from main
git checkout main
git checkout -b hotfix/critical-security-fix

# 2. Fix and test
git commit -m "🚨 Fix critical security issue"

# 3. Merge to main
git checkout main
git merge hotfix/critical-security-fix
git tag -a v2.5.1 -m "Hotfix version 2.5.1"

# 4. Merge to development
git checkout development
git merge hotfix/critical-security-fix

# 5. Push and cleanup
git push origin main
git push origin development
git push origin v2.5.1
git branch -d hotfix/critical-security-fix
```

## 🏷️ Commit Message Convention

### **Format**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### **Types**
- ✨ `feat`: New feature
- 🐛 `fix`: Bug fix
- 📚 `docs`: Documentation
- 💄 `style`: Formatting, missing semi colons, etc.
- ♻️ `refactor`: Code refactoring
- ⚡ `perf`: Performance improvements
- 🧪 `test`: Adding tests
- 🔧 `chore`: Maintenance tasks
- 🚀 `release`: Release commits

### **Examples**
```bash
git commit -m "✨ feat(gui): add dark theme support"
git commit -m "🐛 fix(automation): resolve sequence timing issue"
git commit -m "📚 docs(api): update SCPI command documentation"
git commit -m "♻️ refactor(core): optimize data processing pipeline"
```

## 🛡️ Branch Protection Rules

### **main branch**
- ✅ Require pull request reviews (1+ reviewers)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Restrict pushes that create new files
- ✅ Require linear history

### **development branch**
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ⚠️ Allow force pushes (with caution)

## 📊 Branch Metrics

### **Current Statistics**
- **Total Branches:** 4 (2 main, 2 feature)
- **Active Development:** 3 branches
- **Code Coverage:** 100% (Phase 2.5 complete)
- **Last Release:** v2.5.0 (Production Ready)

## 🎯 Future Branch Planning

### **Planned Feature Branches**
1. `feature/network-connectivity` - Remote control capabilities
2. `feature/cloud-integration` - Cloud data storage
3. `feature/mobile-app` - Mobile companion app
4. `feature/ai-analysis` - Machine learning integration
5. `feature/multi-instrument` - Multi-device coordination

### **Release Schedule**
- **v2.6.0** - Network connectivity (Q4 2025)
- **v2.7.0** - Cloud integration (Q1 2026)
- **v3.0.0** - Major architecture updates (Q2 2026)

## 🔗 Integration Points

### **Continuous Integration**
- **GitHub Actions:** Automated testing on all branches
- **Code Quality:** SonarQube analysis
- **Security:** Dependency vulnerability scanning
- **Documentation:** Auto-generated API docs

### **Deployment Pipeline**
- **Development:** Auto-deploy to staging environment
- **Main:** Auto-deploy to production environment
- **Feature:** Deploy to feature-specific environments

---

## 📞 Support & Guidelines

### **Need Help?**
- Check existing branches: `git branch -a`
- Current branch: `git branch --show-current`
- Branch history: `git log --oneline --graph`

### **Best Practices**
1. **Always** pull latest changes before creating new branch
2. **Never** commit directly to `main` or `development`
3. **Always** create PR for code review
4. **Delete** merged feature branches
5. **Use** descriptive branch names
6. **Test** thoroughly before merging

---

*Branching Strategy Document*  
*Created: September 8, 2025*  
*Version: 1.0*  
*Last Updated: September 8, 2025*
