# CONTRIBUTING.md

## How to Contribute

Thank you for your interest in contributing to the Collatz Engine project!

### Benchmark Submissions (Everyone Welcome!)

We welcome benchmark results from **any hardware** - GPU or CPU!

**Steps:**
1. Run the benchmark: `python benchmark.py`
2. A file named `benchmark_results_YYYYMMDD_HHMMSS.json` will be created
3. The benchmark will indicate if your system was optimized or not
4. Fork this repository on GitHub
5. Rename the file to include your hardware: 
   - GPU: `benchmark_RTX4090_20251023.json`
   - CPU: `benchmark_EPYC7763_128core_20251023.json`
6. Add the file to the `benchmarks/` directory
7. Create a pull request with **ONLY** the benchmark file
   - ⚠️ **Do NOT modify any other files**
   - ⚠️ **Do NOT add multiple files in one PR**
   - One benchmark file per pull request

**For best results:**
- Join the distributed network: `python network_launcher.py`
- Run verification for at least 24 hours
- Export your contribution stats for the benchmark

**What hardware is useful?**
- **Any CUDA GPU** (GTX 1060 to H100 - all data points help!)
- **Any CPU** (especially 16+ cores: dual Xeon, EPYC, Threadripper)
- Both old and new hardware welcomed!

**What to expect:**
- Your PR will be reviewed for the benchmark file only
- If you've modified other files, you'll be asked to remove those changes
- Valid benchmark files will be merged quickly
- Your contribution will be acknowledged!

### Code Contributions

For code changes, optimizations, or bug fixes:

1. **Open an issue first** to discuss the change
2. Wait for approval before starting work
3. Fork the repository
4. Create a feature branch: `git checkout -b feature/your-feature-name`
5. Make your changes
6. Test thoroughly on your hardware
7. Commit with clear messages
8. Push to your fork
9. Create a pull request with:
   - Clear description of changes
   - Why the change is needed
   - Test results on your system

**Code Contribution Guidelines:**
- Follow existing code style
- Add comments for complex logic
- Ensure ASCII-only output (no Unicode characters)
- Test on both GPU and CPU-only configurations if possible
- Don't break backwards compatibility with existing state files
- Run diagnostics to ensure no errors: `python run_diagnostics.py`
- Check that error handling works properly
- Verify auto-resume functionality if modifying optimization code

### What We're Looking For

**High Priority:**
- Benchmark results from diverse GPUs (especially high-end cards)
- Bug reports with reproducible steps
- Performance optimizations with measured improvements
- Documentation improvements

**Please Open an Issue First:**
- New features
- Major refactoring
- Changes to file formats
- UI/output changes

### Code of Conduct

- Be respectful and constructive
- Focus on the math and optimization
- Share knowledge and help others
- Give credit where due

### Questions?

Open an issue with the `question` label or start a discussion!

### License

By contributing, you agree that your contributions will be licensed under the same CC BY-NC-SA 4.0 license as the project.

---

**Special Thanks** to all benchmark contributors - your data helps make this project better for everyone!
