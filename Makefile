#===============================================================================
# Usage:
# General usage:
# 	make check-all
# 	make fix-all
# 	make pre-commit-all
#
#  NOTE: You can also run individual checks or fixes
#===============================================================================
CHECK_TARGETS := \
	check-added-large-files \
	check-ast \
	check-case-conflict \
	check-docstring-first \
	check-merge-conflict \
	check-symlinks \
	check-xml \
	check-yaml \
	check-pep257 \
	check-flake8 \
	check-pydocstyle \
	check-ament_uncrustify \
	ament_cppcheck \
	check-ament_cpplint \
	check-ament_lint_cmake \
	check-ament_copyright \
	check-ament_xmllint \
	check-doc8 \
	check-rst-backticks \
	check-rst-directive-colons \
	check-rst-inline-touching-normal \
	check-github-workflow \
	check-github-actions \
	check-dependabot

FIX_TARGETS := \
	fix-debug-statements \
	fix-end-of-file-fixer \
	fix-mixed-line-ending \
	fix-requirements-txt-fixer \
	fix-trailing-whitespace \
	fix-byte-order-marker\
	fix-remove-tabs \
	fix-pyupgrade \
	fix-isort \
	fix-autopep8 \
	fix-ament_uncrustify \
	fix-ament_copyright \
	fix-codespell
#===============================================================================
# Standard pre-commit hooks
check-added-large-files:
	pre-commit run --hook-stage manual check-added-large-files --all-files

check-ast:
	pre-commit run --hook-stage manual check-ast --all-files

check-case-conflict:
	pre-commit run --hook-stage manual check-case-conflict --all-files

check-docstring-first:
	pre-commit run --hook-stage manual check-docstring-first --all-files

check-merge-conflict:
	pre-commit run --hook-stage manual check-merge-conflict --all-files

check-symlinks:
	pre-commit run --hook-stage manual check-symlinks --all-files

check-xml:
	pre-commit run --hook-stage manual check-xml --all-files

check-yaml:
	pre-commit run --hook-stage manual check-yaml --all-files

fix-debug-statements :
	pre-commit run --hook-stage manual debug-statements --all-files

fix-end-of-file-fixer:
	pre-commit run --hook-stage manual end-of-file-fixer --all-files

fix-mixed-line-ending:
	pre-commit run --hook-stage manual mixed-line-ending --all-files

fix-requirements-txt-fixer:
	pre-commit run --hook-stage manual requirements-txt-fixer --all-files

fix-trailing-whitespace:
	pre-commit run --hook-stage manual trailing-whitespace --all-files

fix-byte-order-marker:
	pre-commit run --hook-stage manual fix-byte-order-marker --all-files

# 3rd party hooks
fix-remove-tabs:
	pre-commit run --hook-stage manual remove-tabs --all-files
#===============================================================================

## Python hooks
fix-pyupgrade:
	pre-commit run --hook-stage manual pyupgrade --all-files

check-pep257:
	pre-commit run --hook-stage manual ament_pep257 --all-files

fix-isort:
	pre-commit run --hook-stage manual isort --all-files

fix-autopep8:
	pre-commit run --hook-stage manual autopep8 --all-files

check-flake8:
	pre-commit run --hook-stage manual flake8 --all-files

check-pydocstyle:
	pre-commit run --hook-stage manual pydocstyle --all-files
#===============================================================================
# ROS2 - ament fixes
## CPP Hooks
check-ament_uncrustify:
	pre-commit run --hook-stage manual ament_uncrustify --all-files

fix-ament_uncrustify:
	./scripts/hooks/run_fix_ament_uncrustify.sh

check-ament_cppcheck:
	pre-commit run --hook-stage manual ament_cppcheck --all-files

check-ament_cpplint:
	pre-commit run --hook-stage manual ament_cpplint --all-files

check-ament_lint_cmake:
	pre-commit run --hook-stage manual ament_lint_cmake --all-files

check-ament_copyright:
	pre-commit run --hook-stage manual ament_copyright --all-files

fix-ament_copyright:
	./scripts/hooks/run_fix_ament_copyright.sh

check-ament_xmllint:
	pre-commit run --hook-stage manual ament_xmllint --all-files
#===============================================================================
check-doc8:
	pre-commit run --hook-stage manual doc8 --all-files

check-rst-backticks:
	pre-commit run --hook-stage manual rst-backticks --all-files

check-rst-directive-colons:
	pre-commit run --hook-stage manual rst-directive-colons --all-files

check-rst-inline-touching-normal:
	pre-commit run --hook-stage manual rst-inline-touching-normal --all-files
#===============================================================================
fix-codespell:
	pre-commit run --hook-stage manual codespell --all-files

check-github-workflow:
	pre-commit run --hook-stage manual check-github-workflow --all-files

check-github-actions:
	pre-commit run --hook-stage manual check-github-actions --all-files

check-dependabot:
	pre-commit run --hook-stage manual check-dependabot --all-files
#===============================================================================
.PHONY: $(FIX_TARGETS) fix-targets
.PHONY: $(CHECK_TARGETS) check-targets

# Apply some hooks that might change the files
fix-targets:
	@$(foreach target,$(FIX_TARGETS),$(MAKE) $(target);)

check-targets:
	@$(foreach target,$(CHECK_TARGETS),$(MAKE) $(target);)

# Run all hooks - the manual ones might change the files
pre-commit-manual-all:
	pre-commit run --hook-stage manual --all-files
#===============================================================================
check:
	$(MAKE) check-targets

fix:
	@$(MAKE) fix-targets
	@$(MAKE) pre-commit-manual-all
