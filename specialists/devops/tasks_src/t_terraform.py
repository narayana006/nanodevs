from _dsl import C, Q, T, d

TASKS = []
add = TASKS.append
F = "main.tf"
V = C("valid", "HCL parses", file=F)

# ------------------------------------------------------------------------ write
add(T("tf-s3-secure-bucket", "write", "terraform", "medium", """
Write `main.tf` (AWS provider v5 style, separate resources per feature) defining a private S3 bucket for application data: `aws_s3_bucket.data` (bucket `acme-app-data`), `aws_s3_bucket_public_access_block.data`
with all four block/ignore settings true, `aws_s3_bucket_versioning.data` (status Enabled), and `aws_s3_bucket_server_side_encryption_configuration.data` using SSE-KMS (`sse_algorithm = "aws:kms"`) with `bucket_key_enabled = true`.
Every sub-resource must reference the bucket via `aws_s3_bucket.data.id` (no hard-coded names, no deprecated inline `acl`/`versioning` blocks).""",
 {F: d(r"""
resource "aws_s3_bucket" "data" {
  bucket = "acme-app-data"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    bucket_key_enabled = true
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
""")},
 [V, Q("bucket name", F, "resource.aws_s3_bucket.data.bucket", "eq", "acme-app-data"), Q("no inline acl", F, "resource.aws_s3_bucket.data.acl", "missing"), Q("no inline versioning", F, "resource.aws_s3_bucket.data.versioning", "missing"),
  *[Q(f"public access block {k}", F, f"resource.aws_s3_bucket_public_access_block.data.{k}", "eq", True) for k in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")],
  Q("pab references bucket", F, "resource.aws_s3_bucket_public_access_block.data.bucket", "eq", "aws_s3_bucket.data.id"), Q("versioning enabled", F, "resource.aws_s3_bucket_versioning.data.versioning_configuration[*].status", "eq", "Enabled"),
  Q("versioning references bucket", F, "resource.aws_s3_bucket_versioning.data.bucket", "eq", "aws_s3_bucket.data.id"),
  Q("SSE kms", F, "resource.aws_s3_bucket_server_side_encryption_configuration.data.rule[*].apply_server_side_encryption_by_default[*].sse_algorithm", "eq", "aws:kms"),
  Q("bucket key", F, "resource.aws_s3_bucket_server_side_encryption_configuration.data.rule[*].bucket_key_enabled", "eq", True), Q("sse references bucket", F, "resource.aws_s3_bucket_server_side_encryption_configuration.data.bucket", "eq", "aws_s3_bucket.data.id")]))

add(T("tf-variables-outputs", "write", "terraform", "medium", """
Write `variables.tf` for a module: variable `environment` (string, description, validation that it is one of dev/staging/prod using `contains([...], var.environment)` with an `error_message`), variable `instance_count` (number, default 2, validation 1..10),
variable `db_password` (string, `sensitive = true`, NO default), variable `tags` (`map(string)`, default `{}`). Add `outputs.tf`?? -> put everything in `variables.tf`: output `environment` (value `var.environment`) and output `db_endpoint` (value `aws_db_instance.main.endpoint`, `sensitive = true`).
Every variable needs a `description`.""",
 {"variables.tf": d(r"""
variable "environment" {
  type        = string
  description = "Deployment environment"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of dev, staging, prod."
  }
}

variable "instance_count" {
  type        = number
  description = "Number of instances"
  default     = 2
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "instance_count must be between 1 and 10."
  }
}

variable "db_password" {
  type        = string
  description = "Master database password"
  sensitive   = true
}

variable "tags" {
  type        = map(string)
  description = "Extra tags"
  default     = {}
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
""")},
 [C("valid", "HCL parses", file="variables.tf"), Q("environment type", "variables.tf", "variable.environment.type", "eq", "string"), Q("environment validation uses contains", "variables.tf", "variable.environment.validation[*].condition", "regex", r"contains\(\s*\[\s*\"dev\",\s*\"staging\",\s*\"prod\"\s*\]\s*,\s*var\.environment\s*\)"),
  Q("environment error_message", "variables.tf", "variable.environment.validation[*].error_message", "regex", r"\S"), Q("instance_count number default 2", "variables.tf", "variable.instance_count.default", "eq", 2),
  Q("instance_count validation range", "variables.tf", "variable.instance_count.validation[*].condition", "regex", r">=\s*1.*<=\s*10|<=\s*10.*>=\s*1"), Q("db_password sensitive", "variables.tf", "variable.db_password.sensitive", "eq", True),
  Q("db_password has no default", "variables.tf", "variable.db_password.default", "missing"), Q("tags type", "variables.tf", "variable.tags.type", "regex", r"^map\(string\)$"), Q("tags default empty map", "variables.tf", "variable.tags.default", "eq", {}),
  Q("all variables have descriptions", "variables.tf", "description", "regex", r"\S", each="variable.*"), Q("output environment", "variables.tf", "output.environment.value", "eq", "var.environment"),
  Q("output db_endpoint", "variables.tf", "output.db_endpoint.value", "eq", "aws_db_instance.main.endpoint"), Q("db_endpoint sensitive", "variables.tf", "output.db_endpoint.sensitive", "eq", True)]))

add(T("tf-sg-web", "write", "terraform", "easy", """
Write `main.tf` with `aws_security_group.web` in the VPC `var.vpc_id`: HTTPS (tcp 443) open to the world (`0.0.0.0/0`), SSH (tcp 22) allowed ONLY from `var.admin_cidr` (a variable, never 0.0.0.0/0), and all outbound traffic allowed (egress `protocol = "-1"`, from/to port 0, `0.0.0.0/0`).
Give it a `name_prefix = "web-"`, a description on the group and on every rule, and `tags = { Name = "web" }`. Declare `variable "vpc_id"` and `variable "admin_cidr"` (type string, no default).""",
 {F: d(r"""
variable "vpc_id" {
  type = string
}

variable "admin_cidr" {
  type = string
}

resource "aws_security_group" "web" {
  name_prefix = "web-"
  description = "Web tier"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from admin network"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web"
  }
}
""")},
 [V, Q("name_prefix", F, "resource.aws_security_group.web.name_prefix", "eq", "web-"), Q("vpc_id var", F, "resource.aws_security_group.web.vpc_id", "eq", "var.vpc_id"), Q("group description", F, "resource.aws_security_group.web.description", "regex", r"\S"),
  Q("443 world open", F, "resource.aws_security_group.web.ingress[*].from_port", "eq", 443, mode="any"), Q("ssh from admin_cidr only", F, "resource.aws_security_group.web.ingress[*].cidr_blocks[*]", "eq", "var.admin_cidr", mode="any"),
  C("not_contains", "no SSH rule that includes 0.0.0.0/0", file=F, regex=r"from_port\s*=\s*22[^}]*0\.0\.0\.0/0"),
  Q("egress all", F, "resource.aws_security_group.web.egress[*].protocol", "eq", "-1"), Q("all rules described", F, "description", "regex", r"\S", each="resource.aws_security_group.web.ingress[*]"),
  Q("egress described", F, "description", "regex", r"\S", each="resource.aws_security_group.web.egress[*]"), Q("Name tag", F, "resource.aws_security_group.web.tags.Name", "eq", "web"),
  Q("admin_cidr variable string", F, "variable.admin_cidr.type", "eq", "string"), Q("admin_cidr has no default", F, "variable.admin_cidr.default", "missing"), Q("vpc_id variable", F, "variable.vpc_id.type", "eq", "string")]))

add(T("tf-ec2-hardened", "write", "terraform", "medium", """
Write `main.tf` with `aws_instance.app` (`ami = var.ami_id`, `instance_type = "t3.small"`, `subnet_id = var.subnet_id`) hardened: IMDSv2 only (`metadata_options { http_tokens = "required" http_endpoint = "enabled" http_put_response_hop_limit = 1 }`),
encrypted root volume (`root_block_device { encrypted = true volume_type = "gp3" volume_size = 20 delete_on_termination = true }`), `monitoring = true`, `ebs_optimized = true`, no public IP (`associate_public_ip_address = false`),
`vpc_security_group_ids = [var.sg_id]`, and tags `Name = "app"` and `Environment = var.environment`. Declare the 5 variables ami_id, subnet_id, sg_id, environment (all strings).""",
 {F: d(r"""
variable "ami_id" { type = string }
variable "subnet_id" { type = string }
variable "sg_id" { type = string }
variable "environment" { type = string }

resource "aws_instance" "app" {
  ami                         = var.ami_id
  instance_type               = "t3.small"
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.sg_id]
  associate_public_ip_address = false
  monitoring                  = true
  ebs_optimized               = true

  metadata_options {
    http_tokens                 = "required"
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted             = true
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "app"
    Environment = var.environment
  }
}
""".replace("variable \"ami_id\" { type = string }\nvariable \"subnet_id\" { type = string }\nvariable \"sg_id\" { type = string }\nvariable \"environment\" { type = string }", 'variable "ami_id" {\n  type = string\n}\n\nvariable "subnet_id" {\n  type = string\n}\n\nvariable "sg_id" {\n  type = string\n}\n\nvariable "environment" {\n  type = string\n}'))},
 [V, Q("IMDSv2 required", F, "resource.aws_instance.app.metadata_options[*].http_tokens", "eq", "required"), Q("hop limit 1", F, "resource.aws_instance.app.metadata_options[*].http_put_response_hop_limit", "eq", 1),
  Q("endpoint enabled", F, "resource.aws_instance.app.metadata_options[*].http_endpoint", "eq", "enabled"), Q("root encrypted", F, "resource.aws_instance.app.root_block_device[*].encrypted", "eq", True),
  Q("gp3 20", F, "resource.aws_instance.app.root_block_device[*].volume_type", "eq", "gp3"), Q("size", F, "resource.aws_instance.app.root_block_device[*].volume_size", "eq", 20), Q("monitoring", F, "resource.aws_instance.app.monitoring", "eq", True),
  Q("ebs_optimized", F, "resource.aws_instance.app.ebs_optimized", "eq", True), Q("no public ip", F, "resource.aws_instance.app.associate_public_ip_address", "eq", False), Q("instance type", F, "resource.aws_instance.app.instance_type", "eq", "t3.small"),
  Q("sg ids", F, "resource.aws_instance.app.vpc_security_group_ids[*]", "eq", "var.sg_id", mode="any"), Q("env tag", F, "resource.aws_instance.app.tags.Environment", "eq", "var.environment"), Q("Name tag", F, "resource.aws_instance.app.tags.Name", "eq", "app"),
  Q("ami var", F, "resource.aws_instance.app.ami", "eq", "var.ami_id"), Q("variables declared", F, "variable.*.type", "eq", "string", mode="all")]))

add(T("tf-provider-backend", "write", "terraform", "medium", """
Write `versions.tf`: a `terraform` block requiring Terraform `~> 1.7`, the AWS provider from `hashicorp/aws` with version constraint `~> 5.40`, and an S3 backend (`bucket = "acme-tfstate"`, `key = "prod/network.tfstate"`, `region = "eu-west-1"`,
`encrypt = true`, `dynamodb_table = "acme-tf-locks"`). Plus `provider "aws"` with `region = var.region` and `default_tags { tags = { ManagedBy = "terraform" } }`, and `variable "region"` (string, default "eu-west-1").""",
 {"versions.tf": d(r"""
terraform {
  required_version = "~> 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }

  backend "s3" {
    bucket         = "acme-tfstate"
    key            = "prod/network.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "acme-tf-locks"
  }
}

variable "region" {
  type    = string
  default = "eu-west-1"
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      ManagedBy = "terraform"
    }
  }
}
""")},
 [C("valid", "HCL parses", file="versions.tf"), Q("required_version", "versions.tf", "terraform.required_version", "eq", "~> 1.7"), Q("aws source", "versions.tf", "terraform.required_providers.aws.source", "eq", "hashicorp/aws"),
  Q("aws version pinned", "versions.tf", "terraform.required_providers.aws.version", "regex", r"^~>\s*5\.40$"), Q("backend bucket", "versions.tf", "terraform.backend.s3.bucket", "eq", "acme-tfstate"),
  Q("backend key", "versions.tf", "terraform.backend.s3.key", "eq", "prod/network.tfstate"), Q("backend encrypt", "versions.tf", "terraform.backend.s3.encrypt", "eq", True),
  Q("backend lock table", "versions.tf", "terraform.backend.s3.dynamodb_table", "eq", "acme-tf-locks"), Q("provider region var", "versions.tf", "provider.aws.region", "eq", "var.region"),
  Q("default tags", "versions.tf", "provider.aws.default_tags[*].tags.ManagedBy", "eq", "terraform"), Q("region variable default", "versions.tf", "variable.region.default", "eq", "eu-west-1")]))

add(T("tf-for-each-subnets", "write", "terraform", "hard", """
Write `main.tf`: variable `subnets` of type `map(object({ cidr = string, az = string }))` (no default). Create `aws_subnet.this` with `for_each = var.subnets` (NOT `count`), `vpc_id = var.vpc_id`, `cidr_block = each.value.cidr`,
`availability_zone = each.value.az`, tags `Name = each.key`. Add output `subnet_ids` whose value is a `for` expression producing a map from subnet key to id: `{ for k, s in aws_subnet.this : k => s.id }`. Declare `variable "vpc_id"` (string).""",
 {F: d(r"""
variable "vpc_id" {
  type = string
}

variable "subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
}

resource "aws_subnet" "this" {
  for_each          = var.subnets
  vpc_id            = var.vpc_id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = {
    Name = each.key
  }
}

output "subnet_ids" {
  value = { for k, s in aws_subnet.this : k => s.id }
}
""")},
 [V, Q("for_each over var.subnets", F, "resource.aws_subnet.this.for_each", "eq", "var.subnets"), Q("no count", F, "resource.aws_subnet.this.count", "missing"), Q("cidr from each.value", F, "resource.aws_subnet.this.cidr_block", "eq", "each.value.cidr"),
  Q("az from each.value", F, "resource.aws_subnet.this.availability_zone", "eq", "each.value.az"), Q("Name = each.key", F, "resource.aws_subnet.this.tags.Name", "eq", "each.key"), Q("vpc", F, "resource.aws_subnet.this.vpc_id", "eq", "var.vpc_id"),
  Q("subnets has no default", F, "variable.subnets.default", "missing"), Q("subnets type is map(object)", F, "variable.subnets.type", "regex", r"(?s)^map\(object\(\{.*cidr\s*=\s*string.*az\s*=\s*string.*\}\)\)$"),
  Q("output is a for expression over the resource", F, "output.subnet_ids.value", "regex", r"^\{\s*for\s+k,\s*s\s+in\s+aws_subnet\.this\s*:\s*k\s*=>\s*s\.id\s*\}$")]))

# ------------------------------------------------------------------------ fix
add(T("tf-fix-open-sg", "fix", "terraform", "easy", """
Audit finding: this security group exposes SSH and MySQL to the internet. Restrict SSH (22) to `var.admin_cidr` and MySQL (3306) to the application security group (`security_groups = [var.app_sg_id]`, no CIDR).
HTTPS (443) from anywhere stays. Declare the variables `admin_cidr` and `app_sg_id` (strings). Keep the group name, VPC and tags.""",
 {F: d(r"""
variable "admin_cidr" {
  type = string
}

variable "app_sg_id" {
  type = string
}

resource "aws_security_group" "db_access" {
  name   = "db-access"
  vpc_id = "vpc-0abc123"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.app_sg_id]
  }

  tags = {
    Name = "db-access"
  }
}
""")},
 [V, C("not_contains", "SSH open to 0.0.0.0/0", file=F, regex=r"from_port\s*=\s*22\b[^}]*0\.0\.0\.0/0", bug=True), C("not_contains", "MySQL open to 0.0.0.0/0", file=F, regex=r"from_port\s*=\s*3306\b[^}]*0\.0\.0\.0/0", bug=True),
  Q("ssh from admin_cidr", F, "resource.aws_security_group.db_access.ingress[*].cidr_blocks[*]", "eq", "var.admin_cidr", mode="any", bug=True),
  Q("mysql from app sg", F, "resource.aws_security_group.db_access.ingress[*].security_groups[*]", "eq", "var.app_sg_id", mode="any", bug=True),
  Q("https stays open", F, "resource.aws_security_group.db_access.ingress[*].from_port", "eq", 443, mode="any", keep=True), Q("name kept", F, "resource.aws_security_group.db_access.name", "eq", "db-access", keep=True),
  Q("variable admin_cidr", F, "variable.admin_cidr.type", "eq", "string", bug=True), Q("variable app_sg_id", F, "variable.app_sg_id.type", "eq", "string", bug=True)],
 start={F: d(r"""
resource "aws_security_group" "db_access" {
  name   = "db-access"
  vpc_id = "vpc-0abc123"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "db-access"
  }
}
""")}))

add(T("tf-fix-public-bucket", "fix", "terraform", "medium", """
This bucket was flagged by the cloud security scanner (public ACL, no encryption, no versioning, no public access block). Fix it for AWS provider v5: remove the inline `acl = "public-read"`, add the separate resources
`aws_s3_bucket_public_access_block.assets` (all four settings true), `aws_s3_bucket_versioning.assets` (Enabled) and `aws_s3_bucket_server_side_encryption_configuration.assets` (AES256). All reference `aws_s3_bucket.assets.id`.
Keep the bucket name `acme-assets` and its tags.""",
 {F: d(r"""
resource "aws_s3_bucket" "assets" {
  bucket = "acme-assets"

  tags = {
    Team = "web"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
""")},
 [V, Q("no public ACL", F, "resource.aws_s3_bucket.assets.acl", "missing", bug=True), *[Q(f"pab {k}", F, f"resource.aws_s3_bucket_public_access_block.assets.{k}", "eq", True, bug=True) for k in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")],
  Q("versioning", F, "resource.aws_s3_bucket_versioning.assets.versioning_configuration[*].status", "eq", "Enabled", bug=True),
  Q("sse AES256", F, "resource.aws_s3_bucket_server_side_encryption_configuration.assets.rule[*].apply_server_side_encryption_by_default[*].sse_algorithm", "in", ["AES256", "aws:kms"], bug=True),
  Q("refs", F, "resource.aws_s3_bucket_versioning.assets.bucket | resource.aws_s3_bucket_public_access_block.assets.bucket | resource.aws_s3_bucket_server_side_encryption_configuration.assets.bucket", "eq", "aws_s3_bucket.assets.id"),
  Q("bucket name kept", F, "resource.aws_s3_bucket.assets.bucket", "eq", "acme-assets", keep=True), Q("tags kept", F, "resource.aws_s3_bucket.assets.tags.Team", "eq", "web", keep=True)],
 start={F: d(r"""
resource "aws_s3_bucket" "assets" {
  bucket = "acme-assets"
  acl    = "public-read"

  tags = {
    Team = "web"
  }
}
""")}))

add(T("tf-fix-hardcoded-secrets", "fix", "terraform", "medium", """
Secrets are hard-coded in this configuration (AWS keys in the provider block, DB password in the instance). Fix it: the provider must take credentials from the environment/instance role (remove `access_key`/`secret_key` entirely, keep `region`),
and the DB password must come from a sensitive variable `db_password` (type string, `sensitive = true`, no default) referenced as `var.db_password`. Keep the instance settings (`identifier = "orders"`, engine postgres, instance class `db.t3.medium`, allocated storage 50).""",
 {F: d(r"""
variable "db_password" {
  type      = string
  sensitive = true
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_db_instance" "orders" {
  identifier        = "orders"
  engine            = "postgres"
  instance_class    = "db.t3.medium"
  allocated_storage = 50
  username          = "orders"
  password          = var.db_password
}
""")},
 [V, Q("no access_key", F, "provider.aws.access_key", "missing", bug=True), Q("no secret_key", F, "provider.aws.secret_key", "missing", bug=True), C("not_contains", "AWS key literals", file=F, regex=r"AKIA[0-9A-Z]{8,}|wJalr", bug=True),
  Q("password from var", F, "resource.aws_db_instance.orders.password", "eq", "var.db_password", bug=True), Q("db_password sensitive", F, "variable.db_password.sensitive", "eq", True, bug=True),
  Q("db_password no default", F, "variable.db_password.default", "missing"), Q("db_password type", F, "variable.db_password.type", "eq", "string"), Q("region kept", F, "provider.aws.region", "eq", "eu-west-1", keep=True),
  Q("instance settings kept", F, "resource.aws_db_instance.orders.instance_class", "eq", "db.t3.medium", keep=True), Q("storage kept", F, "resource.aws_db_instance.orders.allocated_storage", "eq", 50, keep=True)],
 start={F: d(r"""
provider "aws" {
  region     = "eu-west-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

resource "aws_db_instance" "orders" {
  identifier        = "orders"
  engine            = "postgres"
  instance_class    = "db.t3.medium"
  allocated_storage = 50
  username          = "orders"
  password          = "Sup3rS3cret!"
}
""")}))

add(T("tf-fix-unpinned", "fix", "terraform", "medium", """
`terraform init` pulls whatever is newest, so builds are not reproducible. Pin everything: `required_version = ">= 1.6, < 2.0"`, providers `hashicorp/aws` `~> 5.30` and `hashicorp/random` `~> 3.6` in `required_providers`,
and the module source must reference a tagged release (`git::https://github.com/acme/terraform-vpc.git?ref=v2.4.1`) instead of the default branch. Do not change inputs.""",
 {F: d(r"""
terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

module "vpc" {
  source = "git::https://github.com/acme/terraform-vpc.git?ref=v2.4.1"

  cidr = "10.0.0.0/16"
  name = "core"
}
""")},
 [V, Q("required_version", F, "terraform.required_version", "regex", r">=\s*1\.6.*<\s*2\.0", bug=True), Q("aws pinned", F, "terraform.required_providers.aws.version", "regex", r"^~>\s*5\.30$", bug=True),
  Q("random pinned", F, "terraform.required_providers.random.version", "regex", r"^~>\s*3\.6$", bug=True), Q("module tag", F, "module.vpc.source", "regex", r"\?ref=v\d+\.\d+\.\d+$", bug=True),
  Q("sources kept", F, "terraform.required_providers.aws.source", "eq", "hashicorp/aws", keep=True), Q("inputs kept", F, "module.vpc.cidr", "eq", "10.0.0.0/16", keep=True), Q("name kept", F, "module.vpc.name", "eq", "core", keep=True)],
 start={F: d(r"""
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}

module "vpc" {
  source = "git::https://github.com/acme/terraform-vpc.git"

  cidr = "10.0.0.0/16"
  name = "core"
}
""")}))

add(T("tf-fix-rds-unsafe", "fix", "terraform", "hard", """
A production Postgres instance was defined with dev settings. Fix `aws_db_instance.main` for production without renaming or changing engine/class: not publicly accessible, `storage_encrypted = true` with a KMS key (`kms_key_id = var.kms_key_arn`),
`multi_az = true`, `backup_retention_period = 14`, `deletion_protection = true`, `skip_final_snapshot = false` with `final_snapshot_identifier = "main-final"`, `auto_minor_version_upgrade = true`,
`iam_database_authentication_enabled = true`, and the password from the sensitive variable `db_password` instead of the literal. Declare `kms_key_arn` (string) and `db_password` (string, sensitive).""",
 {F: d(r"""
variable "kms_key_arn" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "main" {
  identifier                          = "main"
  engine                              = "postgres"
  engine_version                      = "16.3"
  instance_class                      = "db.r6g.large"
  allocated_storage                   = 200
  username                            = "app"
  password                            = var.db_password
  publicly_accessible                 = false
  storage_encrypted                   = true
  kms_key_id                          = var.kms_key_arn
  multi_az                            = true
  backup_retention_period             = 14
  deletion_protection                 = true
  skip_final_snapshot                 = false
  final_snapshot_identifier           = "main-final"
  auto_minor_version_upgrade          = true
  iam_database_authentication_enabled = true
}
""")},
 [V, Q("not public", F, "resource.aws_db_instance.main.publicly_accessible", "eq", False, bug=True), Q("encrypted", F, "resource.aws_db_instance.main.storage_encrypted", "eq", True, bug=True),
  Q("kms key", F, "resource.aws_db_instance.main.kms_key_id", "eq", "var.kms_key_arn", bug=True), Q("multi_az", F, "resource.aws_db_instance.main.multi_az", "eq", True, bug=True),
  Q("backup retention", F, "resource.aws_db_instance.main.backup_retention_period", "gte", 14, bug=True), Q("deletion protection", F, "resource.aws_db_instance.main.deletion_protection", "eq", True, bug=True),
  Q("final snapshot", F, "resource.aws_db_instance.main.skip_final_snapshot", "eq", False, bug=True), Q("final snapshot id", F, "resource.aws_db_instance.main.final_snapshot_identifier", "eq", "main-final", bug=True),
  Q("minor upgrades", F, "resource.aws_db_instance.main.auto_minor_version_upgrade", "eq", True, bug=True), Q("iam auth", F, "resource.aws_db_instance.main.iam_database_authentication_enabled", "eq", True, bug=True),
  Q("password var", F, "resource.aws_db_instance.main.password", "eq", "var.db_password", bug=True), Q("db_password sensitive", F, "variable.db_password.sensitive", "eq", True), Q("kms var", F, "variable.kms_key_arn.type", "eq", "string"),
  Q("engine kept", F, "resource.aws_db_instance.main.engine", "eq", "postgres", keep=True), Q("class kept", F, "resource.aws_db_instance.main.instance_class", "eq", "db.r6g.large", keep=True), Q("identifier kept", F, "resource.aws_db_instance.main.identifier", "eq", "main", keep=True)],
 start={F: d(r"""
resource "aws_db_instance" "main" {
  identifier          = "main"
  engine              = "postgres"
  engine_version      = "16.3"
  instance_class      = "db.r6g.large"
  allocated_storage   = 200
  username            = "app"
  password            = "changeme123"
  publicly_accessible = true
  storage_encrypted   = false
  multi_az            = false
  skip_final_snapshot = true
}
""")}))

# ------------------------------------------------------------------------ harden
add(T("tf-harden-iam-policy", "harden", "terraform", "hard", """
This role policy grants `*` on `*`. Replace it with least privilege for a service that only reads objects from one bucket and writes logs to a log group: statement 1: `s3:GetObject` and `s3:ListBucket` on the bucket `arn:aws:s3:::acme-reports` (ListBucket) and
`arn:aws:s3:::acme-reports/*` (GetObject); statement 2: `logs:CreateLogStream` and `logs:PutLogEvents` on `arn:aws:logs:eu-west-1:123456789012:log-group:/app/reports:*`. Use `data "aws_iam_policy_document" "reports"` with `statement` blocks (each with `effect = "Allow"`, `actions`, `resources`)
and `aws_iam_policy.reports` using `policy = data.aws_iam_policy_document.reports.json`. No `*` actions and no bare `*` resources.""",
 {F: d(r"""
data "aws_iam_policy_document" "reports" {
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = ["arn:aws:s3:::acme-reports/*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::acme-reports"]
  }

  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:eu-west-1:123456789012:log-group:/app/reports:*"]
  }
}

resource "aws_iam_policy" "reports" {
  name   = "reports"
  policy = data.aws_iam_policy_document.reports.json
}
""")},
 [V, Q("no wildcard actions", F, "data.aws_iam_policy_document.reports.statement[*].actions[*]", "not_regex", r"^\*$|:\*$", bug=True), Q("no bare wildcard resources", F, "data.aws_iam_policy_document.reports.statement[*].resources[*]", "ne", "*", bug=True),
  Q("effect Allow", F, "data.aws_iam_policy_document.reports.statement[*].effect", "eq", "Allow", bug=True),
  Q("GetObject on objects", F, "data.aws_iam_policy_document.reports.statement[*].resources[*]", "eq", "arn:aws:s3:::acme-reports/*", mode="any", bug=True),
  Q("ListBucket on bucket", F, "data.aws_iam_policy_document.reports.statement[*].resources[*]", "eq", "arn:aws:s3:::acme-reports", mode="any", bug=True),
  Q("s3 actions", F, "data.aws_iam_policy_document.reports.statement[*].actions[*]", "in", ["s3:GetObject", "s3:ListBucket", "logs:CreateLogStream", "logs:PutLogEvents"], bug=True),
  Q("logs resource", F, "data.aws_iam_policy_document.reports.statement[*].resources[*]", "eq", "arn:aws:logs:eu-west-1:123456789012:log-group:/app/reports:*", mode="any", bug=True),
  Q("PutLogEvents", F, "data.aws_iam_policy_document.reports.statement[*].actions[*]", "eq", "logs:PutLogEvents", mode="any"), Q("policy uses the document", F, "resource.aws_iam_policy.reports.policy", "eq", "data.aws_iam_policy_document.reports.json", bug=True),
  Q("policy name kept", F, "resource.aws_iam_policy.reports.name", "eq", "reports", keep=True)],
 start={F: d(r"""
resource "aws_iam_policy" "reports" {
  name = "reports"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}
""")}))

# ------------------------------------------------------------------------ convert
add(T("tf-convert-count-to-for-each", "convert", "terraform", "hard", """
These instances use `count` over a list, so removing a server from the middle of the list destroys and recreates every later server. Convert to `for_each` over a map keyed by server name, preserving behaviour:
`variable "servers"` becomes `map(object({ type = string }))` (no default) and the resource uses `for_each = var.servers`, `instance_type = each.value.type`, `tags = { Name = each.key }`, `ami = var.ami_id`.
Update the output to `{ for k, i in aws_instance.web : k => i.private_ip }`. No `count`, no `count.index`.""",
 {F: d(r"""
variable "ami_id" {
  type = string
}

variable "servers" {
  type = map(object({
    type = string
  }))
}

resource "aws_instance" "web" {
  for_each      = var.servers
  ami           = var.ami_id
  instance_type = each.value.type

  tags = {
    Name = each.key
  }
}

output "private_ips" {
  value = { for k, i in aws_instance.web : k => i.private_ip }
}
""")},
 [V, Q("for_each", F, "resource.aws_instance.web.for_each", "eq", "var.servers"), Q("no count", F, "resource.aws_instance.web.count", "missing"), C("not_contains", "no count.index left", file=F, regex=r"count\.index|\bcount\s*="),
  Q("instance_type from each.value", F, "resource.aws_instance.web.instance_type", "eq", "each.value.type"), Q("Name = each.key", F, "resource.aws_instance.web.tags.Name", "eq", "each.key"), Q("ami", F, "resource.aws_instance.web.ami", "eq", "var.ami_id"),
  Q("servers is a map(object)", F, "variable.servers.type", "regex", r"^map\(object\(\{\s*type\s*=\s*string\s*\}\)\)$"), Q("servers has no default", F, "variable.servers.default", "missing"),
  Q("output for expression", F, "output.private_ips.value", "regex", r"^\{\s*for\s+k,\s*i\s+in\s+aws_instance\.web\s*:\s*k\s*=>\s*i\.private_ip\s*\}$")],
 start={F: d(r"""
variable "ami_id" {
  type = string
}

variable "servers" {
  type = list(object({
    name = string
    type = string
  }))
}

resource "aws_instance" "web" {
  count         = length(var.servers)
  ami           = var.ami_id
  instance_type = var.servers[count.index].type

  tags = {
    Name = var.servers[count.index].name
  }
}

output "private_ips" {
  value = aws_instance.web[*].private_ip
}
""")}))

# ------------------------------------------------------------------------ reasoning (answers as JSON)
add(T("tf-reason-count-removal", "write", "terraform", "hard", """
Terraform reasoning. Current state was created from `servers = ["a", "b", "c"]` with
```
resource "aws_instance" "web" {
  count         = length(var.servers)
  ami           = var.ami
  instance_type = "t3.micro"
  tags          = { Name = var.servers[count.index] }
}
```
so the state holds `aws_instance.web[0]` (Name=a), `[1]` (Name=b), `[2]` (Name=c). The list is changed to `["a", "c"]` (b removed) and `terraform apply` is run.
Write `answer.json` with the keys: `"destroyed"` (list of resource addresses destroyed outright), `"updated_in_place"` (addresses whose tags change in place), `"unchanged"` (addresses with no change), and
`"safer_alternative"` (one of the strings `"for_each"` or `"count"`: the meta-argument that would have destroyed ONLY the instance for `b`). Only addresses of the form `aws_instance.web[<index>]`, sorted ascending.""",
 {"answer.json": '{"destroyed": ["aws_instance.web[2]"], "updated_in_place": ["aws_instance.web[1]"], "unchanged": ["aws_instance.web[0]"], "safer_alternative": "for_each"}\n'},
 [C("valid", "valid JSON", file="answer.json"), Q("destroyed", "answer.json", "destroyed", "eq", ["aws_instance.web[2]"]), Q("updated in place", "answer.json", "updated_in_place", "eq", ["aws_instance.web[1]"]),
  Q("unchanged", "answer.json", "unchanged", "eq", ["aws_instance.web[0]"]), Q("alternative", "answer.json", "safer_alternative", "eq", "for_each")]))

add(T("tf-reason-plan-summary", "write", "terraform", "medium", """
Read this `terraform plan` excerpt and classify the resources.
```
  # aws_instance.api will be updated in-place
  ~ resource "aws_instance" "api" { ~ tags = { ~ "Version" = "1" -> "2" } }
  # aws_db_instance.main must be replaced
-/+ resource "aws_db_instance" "main" { ~ identifier = "main" -> "primary" # forces replacement }
  # aws_s3_bucket.logs will be destroyed
  - resource "aws_s3_bucket" "logs" { - bucket = "acme-logs" }
  # aws_sqs_queue.jobs will be created
  + resource "aws_sqs_queue" "jobs" { + name = "jobs" }
  # aws_sns_topic.alerts will be updated in-place
  ~ resource "aws_sns_topic" "alerts" { ~ display_name = "old" -> "new" }
Plan: 2 to add, 2 to change, 2 to destroy.
```
Write `answer.json` with keys `"created"`, `"updated"`, `"destroyed"`, `"replaced"` (each a sorted list of resource addresses; a replaced resource appears ONLY under `replaced`), and `"data_loss_risk"`: the address of the resource whose replacement/destruction is most likely to cause data loss for a stateful
service that is not an S3 bucket being intentionally removed (choose exactly one address) - plus `"counts_match_plan"`: true if your created+replaced and updated and destroyed+replaced numbers agree with the plan summary line (to add / to change / to destroy), else false.""",
 {"answer.json": '{"created": ["aws_sqs_queue.jobs"], "updated": ["aws_instance.api", "aws_sns_topic.alerts"], "destroyed": ["aws_s3_bucket.logs"], "replaced": ["aws_db_instance.main"], "data_loss_risk": "aws_db_instance.main", "counts_match_plan": true}\n'},
 [C("valid", "valid JSON", file="answer.json"), Q("created", "answer.json", "created", "eq", ["aws_sqs_queue.jobs"]), Q("updated", "answer.json", "updated", "eq", ["aws_instance.api", "aws_sns_topic.alerts"]),
  Q("destroyed", "answer.json", "destroyed", "eq", ["aws_s3_bucket.logs"]), Q("replaced", "answer.json", "replaced", "eq", ["aws_db_instance.main"]), Q("data loss risk", "answer.json", "data_loss_risk", "eq", "aws_db_instance.main"),
  Q("counts", "answer.json", "counts_match_plan", "eq", True)]))
