# generated by datamodel-codegen:
#   filename:  https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json
#   timestamp: 2024-10-17T17:07:10+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, RootModel, conint, constr


class Cgroup(Enum):
    host = 'host'
    private = 'private'


class CredentialSpec(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    config: str | None = None
    file: str | None = None
    registry: str | None = None


class Condition(Enum):
    service_started = 'service_started'
    service_healthy = 'service_healthy'
    service_completed_successfully = 'service_completed_successfully'


class DependsOn(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    restart: bool | str | None = None
    required: bool | None = True
    condition: Condition


class Devices(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    source: str
    target: str | None = None
    permissions: str | None = None


class Extends(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    service: str
    file: str | None = None


class Logging(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    driver: str | None = None
    options: Mapping[constr(pattern=r'^.+$'), str | float | None] | None = None


class Ports(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = None
    mode: str | None = None
    host_ip: str | None = None
    target: int | str | None = None
    published: str | int | None = None
    protocol: str | None = None
    app_protocol: str | None = None


class PullPolicy(Enum):
    always = 'always'
    never = 'never'
    if_not_present = 'if_not_present'
    build = 'build'
    missing = 'missing'


class Selinux(Enum):
    z = 'z'
    Z = 'Z'


class Bind(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    propagation: str | None = None
    create_host_path: bool | str | None = None
    selinux: Selinux | None = None


class Volume1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    nocopy: bool | str | None = None
    subpath: str | None = None


class Tmpfs(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    size: conint(ge=0) | str | None = None
    mode: float | str | None = None


class Volumes(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    type: str
    source: str | None = None
    target: str | None = None
    read_only: bool | str | None = None
    consistency: str | None = None
    bind: Bind | None = None
    volume: Volume1 | None = None
    tmpfs: Tmpfs | None = None


class Healthcheck(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    disable: bool | str | None = None
    interval: str | None = None
    retries: float | str | None = None
    test: str | Sequence[str] | None = None
    timeout: str | None = None
    start_period: str | None = None
    start_interval: str | None = None


class Action(Enum):
    rebuild = 'rebuild'
    sync = 'sync'
    sync_restart = 'sync+restart'


class WatchItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    ignore: Sequence[str] | None = None
    path: str
    action: Action
    target: str | None = None


class Development(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    watch: Sequence[WatchItem] | None = None


class Order(Enum):
    start_first = 'start-first'
    stop_first = 'stop-first'


class RollbackConfig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    parallelism: int | str | None = None
    delay: str | None = None
    failure_action: str | None = None
    monitor: str | None = None
    max_failure_ratio: float | str | None = None
    order: Order | None = None


class UpdateConfig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    parallelism: int | str | None = None
    delay: str | None = None
    failure_action: str | None = None
    monitor: str | None = None
    max_failure_ratio: float | str | None = None
    order: Order | None = None


class Limits(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    cpus: float | str | None = None
    memory: str | None = None
    pids: int | str | None = None


class RestartPolicy(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    condition: str | None = None
    delay: str | None = None
    max_attempts: int | str | None = None
    window: str | None = None


class Preference(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    spread: str | None = None


class Placement(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    constraints: Sequence[str] | None = None
    preferences: Sequence[Preference] | None = None
    max_replicas_per_node: int | str | None = None


class DiscreteResourceSpec(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    kind: str | None = None
    value: float | str | None = None


class GenericResource(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    discrete_resource_spec: DiscreteResourceSpec | None = None


class ConfigItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    subnet: str | None = None
    ip_range: str | None = None
    gateway: str | None = None
    aux_addresses: Mapping[constr(pattern=r'^.+$'), str] | None = None


class Ipam(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    driver: str | None = None
    config: Sequence[ConfigItem] | None = None
    options: Mapping[constr(pattern=r'^.+$'), str] | None = None


class External(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = None


class External2(BaseModel):
    name: str | None = None


class EnvFile1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    path: str
    required: bool | str | None = True


class BlkioLimit(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    path: str | None = None
    rate: int | str | None = None


class BlkioWeight(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    path: str | None = None
    weight: int | str | None = None


class ServiceConfigOrSecret1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    source: str | None = None
    target: str | None = None
    uid: str | None = None
    gid: str | None = None
    mode: float | str | None = None


class Ulimits1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    hard: int | str
    soft: int | str


class Constraints(RootModel[Any]):
    root: Any


class Build(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    context: str | None = None
    dockerfile: str | None = None
    dockerfile_inline: str | None = None
    entitlements: Sequence[str] | None = None
    args: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    ssh: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    cache_from: Sequence[str] | None = None
    cache_to: Sequence[str] | None = None
    no_cache: bool | str | None = None
    additional_contexts: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    network: str | None = None
    pull: bool | str | None = None
    target: str | None = None
    shm_size: int | str | None = None
    extra_hosts: (
        Mapping[constr(pattern=r'.+'), str | Sequence[Any]] | Sequence[str] | None
    ) = None
    isolation: str | None = None
    privileged: bool | str | None = None
    secrets: Sequence[str | ServiceConfigOrSecret1] | None = None
    tags: Sequence[str] | None = None
    ulimits: Mapping[constr(pattern=r'^[a-z]+$'), int | str | Ulimits1] | None = None
    platforms: Sequence[str] | None = None


class BlkioConfig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    device_read_bps: Sequence[BlkioLimit] | None = None
    device_read_iops: Sequence[BlkioLimit] | None = None
    device_write_bps: Sequence[BlkioLimit] | None = None
    device_write_iops: Sequence[BlkioLimit] | None = None
    weight: int | str | None = None
    weight_device: Sequence[BlkioWeight] | None = None


class Networks(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    aliases: Sequence[str] | None = None
    ipv4_address: str | None = None
    ipv6_address: str | None = None
    link_local_ips: Sequence[str] | None = None
    mac_address: str | None = None
    driver_opts: Mapping[constr(pattern=r'^.+$'), str | float] | None = None
    priority: float | None = None


class Device(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    capabilities: Sequence[str] | None = None
    count: str | int | None = None
    device_ids: Sequence[str] | None = None
    driver: str | None = None
    options: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None


class Network(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = None
    driver: str | None = None
    driver_opts: Mapping[constr(pattern=r'^.+$'), str | float] | None = None
    ipam: Ipam | None = None
    external: External | None = None
    internal: bool | str | None = None
    enable_ipv6: bool | str | None = None
    attachable: bool | str | None = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None


class Volume(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = None
    driver: str | None = None
    driver_opts: Mapping[constr(pattern=r'^.+$'), str | float] | None = None
    external: External | None = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None


class Secret(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = None
    environment: str | None = None
    file: str | None = None
    external: External2 | None = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    driver: str | None = None
    driver_opts: Mapping[constr(pattern=r'^.+$'), str | float] | None = None
    template_driver: str | None = None


class Config(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str | None = None
    content: str | None = None
    environment: str | None = None
    file: str | None = None
    external: External2 | None = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    template_driver: str | None = None


class Reservations(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    cpus: float | str | None = None
    memory: str | None = None
    generic_resources: Sequence[GenericResource] | None = None
    devices: Sequence[Device] | None = None


class Resources(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    limits: Limits | None = None
    reservations: Reservations | None = None


class Deployment(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    mode: str | None = None
    endpoint_mode: str | None = None
    replicas: int | str | None = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    rollback_config: RollbackConfig | None = None
    update_config: UpdateConfig | None = None
    resources: Resources | None = None
    restart_policy: RestartPolicy | None = None
    placement: Placement | None = None


class Include1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    path: str | Sequence[str] | None = None
    env_file: str | Sequence[str] | None = None
    project_directory: str | None = None


class Service(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    develop: Development | None = None
    deploy: Deployment | None = None
    annotations: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    attach: bool | str | None = None
    build: str | Build | None = None
    blkio_config: BlkioConfig | None = None
    cap_add: Sequence[str] | None = None
    cap_drop: Sequence[str] | None = None
    cgroup: Cgroup | None = None
    cgroup_parent: str | None = None
    command: str | Sequence[str] | None = None
    configs: Sequence[str | ServiceConfigOrSecret1] | None = None
    container_name: str | None = None
    cpu_count: str | conint(ge=0) | None = None
    cpu_percent: str | conint(ge=0, le=100) | None = None
    cpu_shares: float | str | None = None
    cpu_quota: float | str | None = None
    cpu_period: float | str | None = None
    cpu_rt_period: float | str | None = None
    cpu_rt_runtime: float | str | None = None
    cpus: float | str | None = None
    cpuset: str | None = None
    credential_spec: CredentialSpec | None = None
    depends_on: (
        Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), DependsOn] | Sequence[str] | None
    ) = None
    device_cgroup_rules: Sequence[str] | None = None
    devices: Sequence[str | Devices] | None = None
    dns: str | Sequence[str] | None = None
    dns_opt: Sequence[str] | None = None
    dns_search: str | Sequence[str] | None = None
    domainname: str | None = None
    entrypoint: str | Sequence[str] | None = None
    env_file: str | Sequence[str | EnvFile1] | None = None
    environment: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    expose: Sequence[str | float] | None = None
    extends: str | Extends | None = None
    external_links: Sequence[str] | None = None
    extra_hosts: (
        Mapping[constr(pattern=r'.+'), str | Sequence[Any]] | Sequence[str] | None
    ) = None
    group_add: Sequence[str | float] | None = None
    healthcheck: Healthcheck | None = None
    hostname: str | None = None
    image: str | None = None
    init: bool | str | None = None
    ipc: str | None = None
    isolation: str | None = None
    labels: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    links: Sequence[str] | None = None
    logging: Logging | None = None
    mac_address: str | None = None
    mem_limit: float | str | None = None
    mem_reservation: str | int | None = None
    mem_swappiness: int | str | None = None
    memswap_limit: float | str | None = None
    network_mode: str | None = None
    networks: (
        Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Networks | None]
        | Sequence[str]
        | None
    ) = None
    oom_kill_disable: bool | str | None = None
    oom_score_adj: str | conint(ge=-1000, le=1000) | None = None
    pid: str | None = None
    pids_limit: float | str | None = None
    platform: str | None = None
    ports: Sequence[float | str | Ports] | None = None
    privileged: bool | str | None = None
    profiles: Sequence[str] | None = None
    pull_policy: PullPolicy | None = None
    read_only: bool | str | None = None
    restart: str | None = None
    runtime: str | None = None
    scale: int | str | None = None
    security_opt: Sequence[str] | None = None
    shm_size: float | str | None = None
    secrets: Sequence[str | ServiceConfigOrSecret1] | None = None
    sysctls: (
        Mapping[constr(pattern=r'.+'), str | float | bool | None] | Sequence[str] | None
    ) = None
    stdin_open: bool | str | None = None
    stop_grace_period: str | None = None
    stop_signal: str | None = None
    storage_opt: Mapping[str, Any] | None = None
    tmpfs: str | Sequence[str] | None = None
    tty: bool | str | None = None
    ulimits: Mapping[constr(pattern=r'^[a-z]+$'), int | str | Ulimits1] | None = None
    user: str | None = None
    uts: str | None = None
    userns_mode: str | None = None
    volumes: Sequence[str | Volumes] | None = None
    volumes_from: Sequence[str] | None = None
    working_dir: str | None = None


class ComposeSpecification(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    version: str | None = Field(
        None, description='declared for backward compatibility, ignored.'
    )
    name: str | None = Field(
        None,
        description='define the Compose project name, until user defines one explicitly.',
    )
    include: Sequence[str | Include1] | None = Field(
        None, description='compose sub-projects to be included.'
    )
    services: Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Service] | None = None
    networks: Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Network | None] | None = (
        None
    )
    volumes: Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Volume | None] | None = None
    secrets: Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Secret] | None = None
    configs: Mapping[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Config] | None = None
